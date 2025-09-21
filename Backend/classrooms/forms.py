from django import forms
from .models import Classroom, Schedule
from accounts.models import User
from courses.models import Lesson

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "course", "supervisor", "duration_weeks", "description", "class_code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supervisor"].queryset = User.objects.filter(role=User.Roles.INSTRUCTOR)

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ["day", "lesson", "start_time", "end_time"]

    def __init__(self, *args, **kwargs):
        classroom = kwargs.pop("classroom", None)
        super().__init__(*args, **kwargs)

        if classroom and classroom.course_id:
            self.fields["lesson"].queryset = Lesson.objects.filter(course=classroom.course)
        else:
            self.fields["lesson"].queryset = Lesson.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data
