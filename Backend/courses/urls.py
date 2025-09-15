from django.urls import path

from .views import (
    CourseCreateView,
    CourseListView,
    CourseDetailView,
    course_enroll,
    course_instructor_list,
    CourseUpdateView,
    course_delete,
    student_courses,
    available_courses,
    LessonCreateView,
    LessonDetailView,
    SectionCreateView,
    toggle_section_progress,
)

urlpatterns = [
    path("instructor/courses/new/", CourseCreateView.as_view(), name="course_create"),
    path("instructor/courses/", course_instructor_list, name="instructor_courses"),
    path("instructor/courses/<int:pk>/edit/", CourseUpdateView.as_view(), name="course_edit"),
    path("instructor/courses/<int:pk>/delete/", course_delete, name="course_delete"),
    path("instructor/courses/<int:course_id>/lessons/new/", LessonCreateView.as_view(), name="lesson_create"),
    path("instructor/lessons/<int:lesson_id>/sections/new/", SectionCreateView.as_view(), name="section_create"),
    path("lessons/<int:pk>/", LessonDetailView.as_view(), name="lesson_detail"),
    path("lessons/sections/<int:section_id>/toggle/", toggle_section_progress, name="toggle_section_progress"),
    path("courses/<int:pk>/", CourseDetailView.as_view(), name="course_detail"),
    path("courses/<int:course_id>/enroll/", course_enroll, name="course_enroll"),
    path("student/courses/", student_courses, name="student_courses"),
    path("student/courses/available/", available_courses, name="available_courses"),
]
