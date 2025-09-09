from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required

from .models import Course, Enrollment

class InstructorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.groups.filter(name="Instructor").exists()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseForbidden("Instructor role required")

class CourseCreateView(InstructorRequiredMixin, CreateView):
    model = Course
    fields = ["title", "course_code", "description", "credit_points", "status"]
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("courses")

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        # If "publish" button pressed, publish immediately
        if "publish" in self.request.POST:
            form.instance.is_draft = False
            form.instance.published_at = timezone.now()
            messages.success(self.request, "Course created and published")
        else:
            form.instance.is_draft = True
            messages.success(self.request, "Course saved as draft")
        return super().form_valid(form)

class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    """Allow instructors to edit a course and publish drafts."""
    model = Course
    fields = ["title", "course_code", "description", "credit_points", "status"]
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("courses")

    def form_valid(self, form):
        if "publish" in self.request.POST:
            form.instance.is_draft = False
            form.instance.published_at = timezone.now()
            messages.success(self.request, "Course published")
        else:
            messages.success(self.request, "Course updated")
        return super().form_valid(form)

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/course_list.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.groups.filter(name="Instructor").exists():
            # Instructors see all their own courses (draft + published)
            return Course.objects.filter(instructor=user)
        # Students see only published courses
        return Course.objects.filter(is_draft=False)

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "courses/course_detail.html"

    def get_queryset(self):
        qs = Course.objects.all()
        user = self.request.user
        if not user.groups.filter(name="Instructor").exists():
            qs = qs.filter(is_draft=False)  # Students cannot access drafts
        return qs

@login_required
def course_enroll(request, course_id):
    """Allow students to enroll in a published course."""
    course = get_object_or_404(Course, id = course_id)

    # Prevent enrollment in draft courses
    if course.is_draft and not request.user.groups.filter(name="Instructor").exists():
        messages.error(request, "This course is not published yet.")
        return redirect("courses")

    _, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    if created:
        messages.success(request, f"You have successfully enrolled in {course.title}")
    else:
        messages.info(request, f"You are already enrolled in {course.title}")

    return redirect("courses")
