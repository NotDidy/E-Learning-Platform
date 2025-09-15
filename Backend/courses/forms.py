from django import forms

from .models import Lesson, Section


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "learning_objectives",
            "reading_list",
            "order",
        ]


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = [
            "title",
            "content",
            "order",
        ]

