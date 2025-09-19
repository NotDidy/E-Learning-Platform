from django import forms
from .models import Classroom, Schedule


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "course", "supervisor", "duration_weeks", "description", "class_code"]

    def clean_duration_weeks(self):
        duration = self.cleaned_data["duration_weeks"]
        if duration < 1:
            raise forms.ValidationError("Duration must be at least 1 week.")
        return duration


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ["day", "lesson", "start_time", "end_time"]

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data