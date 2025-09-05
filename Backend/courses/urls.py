from django.urls import path

from .views import (
    CourseCreateView,
)

urlpatterns = [
    path("instructor/courses/new/", CourseCreateView.as_view(), name="course_create"),
]