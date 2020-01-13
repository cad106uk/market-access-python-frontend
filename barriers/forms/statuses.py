from django import forms
from django.template.loader import render_to_string

from utils.api_client import MarketAccessAPIClient
from utils.forms import ChoiceFieldWithHelpText, MonthYearField
from utils.metadata import (
    OPEN_PENDING_ACTION,
    OPEN_IN_PROGRESS,
    RESOLVED_IN_PART,
    RESOLVED_IN_FULL,
    DORMANT,
    UNKNOWN,
)


class UnknownForm(forms.Form):
    """
    Subform of BarrierStatusForm
    """
    unknown_summary = forms.CharField(
        label="Provide a summary of why this barrier is unknown",
        widget=forms.Textarea,
    )

    def as_html(self):
        template_name = "barriers/forms/statuses/unknown.html"
        return render_to_string(template_name, context={'form': self})

    def get_api_params(self):
        return {
            'status_summary': self.cleaned_data['unknown_summary'],
        }


class OpenPendingForm(forms.Form):
    """
    Subform of BarrierStatusForm
    """
    CHOICES = [
        ("UK_GOVT", 'UK government'),
        ("FOR_GOVT", 'Foreign government'),
        ("BUS", "Affected business"),
        ("OTHER", "Other"),
    ]
    pending_type = forms.ChoiceField(
        label="Who is the action with?",
        choices=CHOICES,
        widget=forms.RadioSelect
    )
    pending_type_other = forms.CharField(
        label="Please specify",
        required=False,
    )
    pending_summary = forms.CharField(
        label="Provide a summary of why this barrier is pending action",
        widget=forms.Textarea,
    )

    def as_html(self):
        template_name = "barriers/forms/statuses/open_pending.html"
        return render_to_string(template_name, context={'form': self})

    def clean(self):
        cleaned_data = super().clean()
        pending_type = cleaned_data.get("pending_type")
        pending_type_other = cleaned_data.get("pending_type_other")

        if pending_type == "OTHER" and not pending_type_other:
            self.add_error(
                "pending_type_other",
                "Enter a description for the pending action"
            )

    def get_api_params(self):
        params = {
            'status_summary': self.cleaned_data['pending_summary'],
            'sub_status': self.cleaned_data['pending_type'],
        }
        if self.cleaned_data.get("pending_type") == "OTHER":
            params.update({
                'sub_status_other': self.cleaned_data['pending_type_other']
            })
        return params


class OpenInProgressForm(forms.Form):
    """
    Subform of BarrierStatusForm
    """
    reopen_summary = forms.CharField(
        label="Provide a summary of why this barrier is being reopened",
        widget=forms.Textarea,
    )

    def as_html(self):
        template_name = "barriers/forms/statuses/open_in_progress.html"
        return render_to_string(template_name, context={'form': self})

    def get_api_params(self):
        return {
            'status_summary': self.cleaned_data['reopen_summary'],
        }


class ResolvedInPartForm(forms.Form):
    """
    Subform of BarrierStatusForm
    """
    part_resolved_date = MonthYearField()
    part_resolved_summary = forms.CharField(
        label="Provide a summary of how this barrier was partially resolved",
        widget=forms.Textarea,
    )

    def as_html(self):
        template_name = "barriers/forms/statuses/resolved_in_part.html"
        return render_to_string(template_name, context={'form': self})

    def get_api_params(self):
        return {
            'status_summary': self.cleaned_data['part_resolved_summary'],
            'status_date': self.cleaned_data['part_resolved_date'].isoformat(),
        }


class ResolvedInFullForm(forms.Form):
    """
    Subform of BarrierStatusForm
    """
    resolved_date = MonthYearField()
    resolved_summary = forms.CharField(
        label="Provide a summary of how this barrier was resolved",
        widget=forms.Textarea,
    )

    def as_html(self):
        template_name = "barriers/forms/statuses/resolved_in_full.html"
        return render_to_string(template_name, context={'form': self})

    def get_api_params(self):
        return {
            'status_summary': self.cleaned_data['resolved_summary'],
            'status_date': self.cleaned_data['resolved_date'].isoformat(),
        }


class DormantForm(forms.Form):
    """
    Subform of BarrierStatusForm
    """
    dormant_summary = forms.CharField(
        label="Provide a summary of why this barrier is dormant",
        widget=forms.Textarea,
    )

    def as_html(self):
        template_name = "barriers/forms/statuses/dormant.html"
        return render_to_string(template_name, context={'form': self})

    def get_api_params(self):
        return {'status_summary': self.cleaned_data['dormant_summary']}


class BarrierStatusForm(forms.Form):
    """
    Form with subforms depending on the radio button selected
    """
    CHOICES = [
        (
            UNKNOWN,
            "Unknown",
            "Barrier requires further work for the status to be known "
        ),
        (
            OPEN_PENDING_ACTION,
            "Open: Pending action",
            "Barrier is awaiting action"
        ), (
            OPEN_IN_PROGRESS,
            "Open: In progress",
            "Barrier is being worked on"
        ), (
            RESOLVED_IN_PART,
            "Resolved: In part",
            "Barrier impact has been significantly reduced but remains in part"
        ), (
            RESOLVED_IN_FULL,
            "Resolved: In full",
            "Barrier has been resolved for all UK companies"
        ), (
            DORMANT,
            "Dormant",
            "Barrier is present but not being pursued"
        ),
    ]
    status = ChoiceFieldWithHelpText(
        label="Change barrier status",
        choices=CHOICES,
        widget=forms.RadioSelect,
    )
    subform_classes = {
        UNKNOWN: UnknownForm,
        OPEN_PENDING_ACTION: OpenPendingForm,
        OPEN_IN_PROGRESS: OpenInProgressForm,
        RESOLVED_IN_PART: ResolvedInPartForm,
        RESOLVED_IN_FULL: ResolvedInFullForm,
        DORMANT: DormantForm,
    }
    subforms = {}

    def __init__(self, barrier, token, *args, **kwargs):
        self.barrier = barrier
        self.token = token
        super().__init__(*args, **kwargs)
        self.remove_current_status_from_choices()
        data = kwargs.get('data')
        for value, subform_class in self.subform_classes.items():
            if data and data.get('status') == value:
                self.subforms[value] = subform_class(data)
            else:
                self.subforms[value] = subform_class()

    def remove_current_status_from_choices(self):
        self.fields['status'].choices = [
            choice
            for choice in self.fields['status'].choices
            if choice[0] != self.barrier.status['id']
        ]

    def status_choices(self):
        for value, name, help_text in self.fields['status'].choices:
            yield {
                'value': value,
                'name': name,
                'help_text': help_text,
                'subform': self.subforms[value],
            }

    def get_subform(self):
        return self.subforms.get(self.cleaned_data['status'])

    def is_valid(self):
        return super().is_valid() and self.get_subform().is_valid()

    def save(self):
        client = MarketAccessAPIClient(self.token)
        subform = self.get_subform()
        client.barriers.set_status(
            barrier_id=self.barrier.id,
            status=self.cleaned_data['status'],
            **subform.get_api_params(),
        )