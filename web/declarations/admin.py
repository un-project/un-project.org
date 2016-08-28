from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.forms import Textarea

from declarations.models import Resolution, Declaration, Report


class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'declaration', 'resolution')


class DeclarationInline(admin.TabularInline):
    model = Declaration
    extra = 0
    fields = ('user', 'declaration_type',
              'text', 'sources', 'is_approved')
    fk_name = "resolution"
    raw_id_fields = ('speaker', )
    formfield_overrides = {
        models.TextField: {
            'widget': Textarea(
                attrs={'rows': 2, 'cols': 40}
            )},
    }


class ResolutionAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'is_featured',
                    'is_published', 'declaration_count')
    list_editable = ('language', 'is_featured',)
    search_fields = ('title', 'nouns__text')
    list_per_page = 100
    list_filter = ('language', 'is_featured',)
    filter_horizontal = ('nouns', 'related_nouns')
    inlines = [DeclarationInline]

    def declaration_count(self, obj):
        return obj.declarations.count()


class DeclarationAdmin(admin.ModelAdmin):
    list_display = ('text', 'resolution', 'is_deleted')
    list_filter = ('is_deleted',)

    def get_queryset(self, request):
        return Declaration.objects.all_with_deleted()


admin.site.register(Report, ReportAdmin)
admin.site.register(Resolution, ResolutionAdmin)
admin.site.register(Declaration, DeclarationAdmin)
