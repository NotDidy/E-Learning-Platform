from django.db import models
from django.conf import settings

class Course(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = (
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
    )

    title = models.CharField(max_length=255)
    course_code = models.CharField(max_length=32, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    credit_points = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses"
    )

    #new field
    is_draft = models.BooleanField(
        default=True,
        help_text="If true, the course is a draft and not visible to students"
    )
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "course"

    def publish(self, when):
            self.is_draft = False
            self.published_at = when
            self.save(update_fields=["is_draft", "published_at"])

    def __str__(self) -> str:
        return self.title
    
class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    date_enrolled = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
                models.UniqueConstraint(fields=["student", "course"], name="unique_enrollment")
            ]

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    learning_objectives = models.TextField(blank=True, help_text="One per line or paragraph")
    reading_list = models.TextField(blank=True, help_text="References or links, one per line")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]
        db_table = "lesson"

    def __str__(self) -> str:
        return f"{self.title} ({self.course.title})"


class Section(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]
        db_table = "lesson_section"

    def __str__(self) -> str:
        return f"{self.title} ({self.lesson.title})"


class SectionProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="section_progress")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="progress")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "section")
        db_table = "section_progress"

    def __str__(self) -> str:
        status = "done" if self.completed else "pending"
        return f"{self.student} - {self.section} [{status}]"
