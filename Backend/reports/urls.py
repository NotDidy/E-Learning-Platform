from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [

    path(
        "instructor/",
        views.instructor_report_list,
        name="instructor_report_list",
    ),

    path(
        "courses/<int:course_id>/students/<int:student_id>/",
        views.student_course_report,
        name="student_course_report",
    ),
]
