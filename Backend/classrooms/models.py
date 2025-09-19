from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from courses.models import Course


class Classroom(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="classrooms"
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="classrooms"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    max_students = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "classroom"

    def __str__(self):
        return f"{self.name} ({self.course.title})"


class ClassroomEnrollment(models.Model):
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="classroom_enrollments"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["classroom", "student"], name="unique_classroom_enrollment"
            )
        ]
        db_table = "classroom_enrollment"

    def __str__(self):
        return f"{self.student} in {self.classroom}"