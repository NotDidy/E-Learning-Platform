from django.urls import path

from .views import (
    CourseCreateView,
    CourseListView,
    CourseDetailView,
    course_enroll,
    course_instructor_list,
    CourseUpdateView,
    course_delete,
)

urlpatterns = [
    path("instructor/courses/new/", CourseCreateView.as_view(), name="course_create"),
    path("instructor/courses/", course_instructor_list, name="instructor_courses"),
    path("instructor/courses/<int:pk>/edit/", CourseUpdateView.as_view(), name="course_edit"),
    path("instructor/courses/<int:pk>/delete/", course_delete, name="course_delete"),
    path("courses/", CourseListView.as_view(), name="courses"),
    path("courses/<int:pk>/", CourseDetailView.as_view(), name="course_detail"),
    path("courses/<int:course_id>/enroll/", course_enroll, name="course_enroll"),
]
