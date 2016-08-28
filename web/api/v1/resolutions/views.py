from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework import filters, status

from declarations.models import Resolution, Declaration
from .serializers import (ResolutionSerializer, DeclarationsSerializer,
                          DeclarationReportSerializer)
from declarations.utils import int_or_default
from declarations.signals import supported_a_declaration
from api.v1.users.serializers import UserProfileSerializer
from newsfeed.models import Entry


class ResolutionViewset(viewsets.ModelViewSet):
    queryset = Resolution.objects.filter(is_published=True)\
                                 .prefetch_related('declarations',
                                                   'declarations__supporters')\
                                 .select_related('user', 'declarations__parent',
                                                 'declarations__user')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = ResolutionSerializer
    paginate_by = 20
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend,
                       filters.OrderingFilter)
    search_fields = ('title',)
    filter_fields = ('is_featured',)
    ordering_fields = ('date_creation',)

    @detail_route()
    def declarations(self, request, pk=None):
        resolution = self.get_object()
        serializer = DeclarationsSerializer(
            resolution.declarations.select_related('user').all(), many=True)
        return Response(serializer.data)

    def create_resolution(self, request):
        serializer = self.serializer_class(
            data=request.data, initial={'ip': request.META['REMOTE_ADDR'],
                                        'user': request.user})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_owner_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {
            self.lookup_field: self.kwargs[lookup_url_kwarg],
            'user': self.request.user
        }
        obj = get_object_or_404(Resolution.objects.all(), **filter_kwargs)
        return obj

    def update_resolution(self, request, pk=None):
        resolution = self._get_owner_object()
        serializer = self.serializer_class(data=request.DATA,
                                           instance=resolution)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_resolution(self, request, pk=None):
        resolution = self._get_owner_object()
        Entry.objects.delete(resolution.get_newsfeed_type(), resolution.id)
        resolution.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route()
    def create_declaration(self, request, pk=None):
        resolution = self.get_object()
        serializer = DeclarationsSerializer(
            data=request.data, initial={'ip': request.META['REMOTE_ADDR'],
                                        'user': request.user,
                                        'resolution': resolution})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeclarationViewset(viewsets.ModelViewSet):
    queryset = Declaration.objects.filter(is_approved=True)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = DeclarationsSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'declaration_id'

    def filter_queryset(self, queryset):
        resolution_id = int_or_default(self.kwargs.get('pk'), default=0)
        return queryset.filter(resolution__id=resolution_id,
                               resolution__is_published=True)

    @detail_route(methods=['post'])
    def report(self, request, pk=None, declaration_id=None):
        declaration = self.get_object()
        if declaration.reports.filter(reporter=request.user).exists():
            return Response({'message': 'Onermeyi Zaten Rapor ettin.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = DeclarationReportSerializer(
            data=request.data, initial={'reporter': request.user,
                                        'declaration': declaration,
                                        'resolution': declaration.resolution})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_owner_object(self):
        resolution_id = int_or_default(self.kwargs.get('pk'), default=0)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {
            self.lookup_field: self.kwargs[lookup_url_kwarg],
            'resolution__id': resolution_id,
            'user': self.request.user
        }
        obj = get_object_or_404(Declaration.objects.all(), **filter_kwargs)
        return obj

    def update_declaration(self, request, pk=None, declaration_id=None):
        declaration = self._get_owner_object()
        serializer = self.serializer_class(data=request.DATA,
                                           instance=declaration)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_declaration(self, request, pk=None, declaration_id=None):
        declaration = self._get_owner_object()
        declaration.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeclarationSupportViewset(DeclarationViewset):

    @detail_route(methods=['post'])
    def support(self, request, pk=None, declaration_id=None):
        declaration = self.get_object()
        if declaration.supporters.filter(id=request.user.id).exists():
            return Response({'message': "Onermeyi Zaten destekliyorsun"},
                            status=status.HTTP_400_BAD_REQUEST)
        declaration.supporters.add(request.user)
        supported_a_declaration.send(sender=self, declaration=declaration,
                                 user=self.request.user)
        return Response(status=status.HTTP_201_CREATED)

    @detail_route(methods=['get'])
    def supporters(self, request, pk=None, declaration_id=None):
        declaration = self.get_object()
        page = self.paginate_queryset(declaration.supporters.all())
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)

    @detail_route(methods=['delete'])
    def unsupport(self, request, pk=None, declaration_id=None):
        declaration = self.get_object()
        if not declaration.supporters.filter(id=request.user.id).exists():
            return Response({'message': "Once onermeyi desteklemen gerekiyor"},
                            status=status.HTTP_400_BAD_REQUEST)
        declaration.supporters.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


resolution_list = ResolutionViewset.as_view(
    {'get': 'list', 'post': 'create_resolution'}
)
resolution_detail = ResolutionViewset.as_view(
    {'get': 'retrieve', 'put': 'update_resolution',
     'delete': 'delete_resolution'}
)
declarations_list = ResolutionViewset.as_view(
    {'get': 'declarations', 'post': 'create_declaration'}
)
declaration_detail = DeclarationViewset.as_view(
    {'get': 'retrieve', 'put': 'update_declaration',
     'delete': 'delete_declaration'}
)
declaration_report = DeclarationViewset.as_view(
    {'post': 'report'}
)
declaration_support = DeclarationSupportViewset.as_view(
    {'post': 'support', 'delete': 'unsupport'}
)
declaration_supporters = DeclarationSupportViewset.as_view(
    {'get': 'supporters'},
    serializer_class=UserProfileSerializer
)
