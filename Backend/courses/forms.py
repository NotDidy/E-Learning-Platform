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
            "prerequisites",
        ]

        def __init__(self, *args, **kwargs):
            course = kwargs.pop("course", None)
            super().__init__(*args, **kwargs)
            if course:
                self.fields["prerequisites"].queryset = course.lessons.exclude(pk=self.instance.pk)


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = [
            "title",
            "content",
            "order",
        ]

