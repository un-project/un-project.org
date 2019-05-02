# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from declarations.constants import MAX_DECLARATION_CONTENT_LENGTH
from declarations.mixins import FormRenderer
from declarations.models import Resolution, Declaration, Report


class ResolutionCreationForm(FormRenderer, forms.ModelForm):
    class Meta:
        model = Resolution
        fields = ["title", "owner", "sources"]


class DeclarationCreationForm(FormRenderer, forms.ModelForm):
    class Meta:
        model = Declaration
        fields = ["declaration_type", "text", "related_resolution", "sources"]
        widgets = {
            "declaration_type": forms.RadioSelect,
            "related_resolution": forms.TextInput,
            "text": forms.Textarea(attrs={"maxlength": MAX_DECLARATION_CONTENT_LENGTH}),
        }

    def clean(self):
        form_data = self.cleaned_data
        if not form_data["related_resolution"] and not form_data["text"]:
            raise ValidationError(
                _("You should write a declaration or link a resolution.")
            )
        return form_data


class DeclarationEditForm(DeclarationCreationForm):
    class Meta:
        model = Declaration
        fields = [
            "declaration_type",
            "text",
            "sources",
            "parent",
            "related_resolution",
            "is_approved",
        ]
        widgets = {
            "declaration_type": forms.RadioSelect,
            "related_resolution": forms.TextInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = self.instance.resolution.declarations.exclude(
            pk=self.instance.pk
        )  # avoid self-loop
        self.fields["parent"].queryset = queryset


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["fallacy_type", "reason"]

    def clean(self):
        is_report_exist = Report.objects.filter(
            reporter=self.initial["reporter"],
            declaration=self.initial["declaration"],
            resolution=self.initial["resolution"],
            fallacy_type=self.cleaned_data["fallacy_type"],
        ).exists()

        if is_report_exist:
            raise ValidationError(
                u"You have already reported %s fallacy for this declaration."
                % (self.cleaned_data["fallacy_type"])
            )

        super().clean()
