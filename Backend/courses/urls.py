from django.urls import path

from .views import (
    CourseCreateView,
    CourseListView,
    CourseDetailView,
    course_enroll
)

urlpatterns = [
    path("instructor/courses/new/", CourseCreateView.as_view(), name="course_create"),
    path("courses/", CourseListView.as_view(), name="courses"),
    path("courses/<int:pk>/", CourseDetailView.as_view(), name="course_detail"),
    path("courses/<int:course_id>/enroll/", course_enroll, name="course_enroll"),
]