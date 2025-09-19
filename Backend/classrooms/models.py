from django.db import models
from datetime import timedelta


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Classroom(models.Model):
    name = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="classrooms")
    supervisor = models.CharField(max_length=200)
    duration_weeks = models.PositiveIntegerField(help_text="Enter the class duration in weeks")
    description = models.TextField(blank=True, null=True)
    class_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def end_date(self):
        return self.created_at.date() + timedelta(weeks=self.duration_weeks)

    def __str__(self):
        return f"{self.name} - {self.course.name}"


class Schedule(models.Model):
    DAYS = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
    ]

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="schedules")
    day = models.CharField(max_length=20, choices=DAYS)
    lesson = models.CharField(max_length=200)  
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.classroom.name} - {self.day} ({self.lesson})"
