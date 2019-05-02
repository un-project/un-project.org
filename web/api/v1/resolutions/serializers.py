from django.urls import reverse

from rest_framework import serializers

from declarations.models import (
    Resolution,
    Declaration,
    Report,
    FALLACY_TYPES,
    DECLARATION_TYPES,
)
from declarations.signals import reported_as_fallacy
from api.v1.users.serializers import UserProfileSerializer


class DeclarationsSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    absolute_url = serializers.SerializerMethodField()
    declaration_type = serializers.ReadOnlyField(source="get_declaration_type_display")
    supporters = UserProfileSerializer(many=True, read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Declaration.objects.all(), required=False
    )
    text = serializers.CharField(required=True, max_length=300)
    declaration_type = serializers.ChoiceField(required=True, choices=DECLARATION_TYPES)

    class Meta:
        model = Declaration
        fields = (
            "id",
            "user",
            "text",
            "sources",
            "parent",
            "absolute_url",
            "declaration_type",
            "date_creation",
            "supporters",
        )
        read_only_fields = ("id", "absolute_url", "date_creation")

    def create(self, validated_data):
        instance = Declaration(**validated_data)
        instance.user = self.initial["user"]
        instance.ip_address = self.initial["ip"]
        instance.resolution = self.initial["resolution"]
        instance.is_approved = True
        instance.save()
        return instance

    def get_absolute_url(self, obj):
        return reverse("api-declaration-detail", args=[obj.resolution.id, obj.id])


class ResolutionSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    declarations = DeclarationsSerializer(many=True, read_only=True)
    absolute_url = serializers.SerializerMethodField()
    report_count = serializers.ReadOnlyField(source="reports.count")
    is_published = serializers.BooleanField(required=True)

    class Meta:
        model = Resolution
        fields = (
            "id",
            "user",
            "title",
            "slug",
            "description",
            "owner",
            "sources",
            "declarations",
            "date_creation",
            "absolute_url",
            "report_count",
            "is_featured",
            "is_published",
        )
        read_only_fields = (
            "id",
            "slug",
            "absolute_url",
            "is_featured",
            "date_creation",
        )

    def create(self, validated_data):
        instance = Resolution(**validated_data)
        instance.user = self.initial["user"]
        instance.ip_address = self.initial["ip"]
        instance.save()
        return instance

    def get_absolute_url(self, obj):
        return reverse("api-resolution-detail", args=[obj.id])


class DeclarationReportSerializer(serializers.ModelSerializer):
    reporter = UserProfileSerializer(read_only=True)
    declaration = DeclarationsSerializer(read_only=True)
    resolution = ResolutionSerializer(read_only=True)
    fallacy_type = serializers.ChoiceField(required=True, choices=FALLACY_TYPES)

    class Meta:
        model = Report
        fields = ("fallacy_type", "reporter", "declaration", "resolution")

    def create(self, validated_data):
        instance = Report(**validated_data)
        instance.reporter = self.initial["reporter"]
        instance.declaration = self.initial["declaration"]
        instance.resolution = self.initial["resolution"]
        instance.save()
        reported_as_fallacy.send(sender=self, report=instance)
        return instance
