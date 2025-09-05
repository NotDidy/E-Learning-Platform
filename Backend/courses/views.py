from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView

from .models import Course

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
        messages.success(self.request, "Course created")
        return super().form_valid(form)
