from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path(
        "courses/<int:course_id>/students/<int:student_id>/",
        views.student_course_report,
        name="student_course_report",
    ),
]
