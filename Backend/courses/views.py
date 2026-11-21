from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from .models import Course, Enrollment

class InstructorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        # Treat users with role attribute == INSTRUCTOR as instructors; fallback to group if present
        try:
            if getattr(user, "role", None) == getattr(user.__class__, "Roles").INSTRUCTOR:  # type: ignore[attr-defined]
                return True
        except Exception:
            pass
        return user.is_authenticated and user.groups.filter(name="Instructor").exists()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseForbidden("Instructor role required")

class CourseCreateView(InstructorRequiredMixin, CreateView):
    model = Course
    fields = ["title", "course_code", "description", "credit_points", "status"]
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("instructor_courses")

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        messages.success(self.request, "Course created")
        return super().form_valid(form)

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/course_list.html"

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "courses/course_detail.html"

@login_required
def course_enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Enforce student-only and max 4 course limit
    user = request.user
    try:
        is_student = getattr(user, "role", None) == user.__class__.Roles.STUDENT  # type: ignore[attr-defined]
    except Exception:
        is_student = False

    if not user.is_authenticated or not is_student:
        return HttpResponseForbidden("Student role required")

    current_count = Enrollment.objects.filter(student=user).count()
    if current_count >= 4:
        messages.error(request, "You have reached the maximum of 4 enrolled courses.")
    else:
        _, created = Enrollment.objects.get_or_create(student=user, course=course)
        if created:
            messages.success(request, f"You have successfully enrolled in {course.title}")
        else:
            messages.info(request, f"You are already enrolled in {course.title}")

    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("available_courses")


@login_required
def student_courses(request):
    """List courses the student is enrolled in."""
    user = request.user
    try:
        is_student = getattr(user, "role", None) == user.__class__.Roles.STUDENT  # type: ignore[attr-defined]
    except Exception:
        is_student = False
    if not is_student:
        return HttpResponseForbidden("Student role required")

    enrollments = (
        Enrollment.objects.filter(student=user)
        .select_related("course", "course__instructor")
    )
    courses = [e.course for e in enrollments]
    return render(request, "courses/course-student.html", {"courses": courses})


@login_required
def available_courses(request):
    """List courses the student is NOT enrolled in, up to max 4 allowed."""
    user = request.user
    try:
        is_student = getattr(user, "role", None) == user.__class__.Roles.STUDENT  # type: ignore[attr-defined]
    except Exception:
        is_student = False
    if not is_student:
        return HttpResponseForbidden("Student role required")

    enrolled_ids = Enrollment.objects.filter(student=user).values_list("course_id", flat=True)
    courses = (
        Course.objects.exclude(id__in=enrolled_ids)
        .annotate(student_count=Count("enrollments"))
        .order_by("-created_at")
    )
    enrolled_count = len(enrolled_ids)
    return render(
        request,
        "courses/available-course.html",
        {"courses": courses, "enrolled_count": enrolled_count, "max_courses": 4},
    )


@login_required
def course_instructor_list(request):
    """List courses owned by the logged-in instructor."""
    user = request.user
    # Simple role check; if not instructor, forbid
    try:
        is_instructor = getattr(user, "role", None) == user.__class__.Roles.INSTRUCTOR  # type: ignore[attr-defined]
    except Exception:
        is_instructor = False
    if not is_instructor:
        return HttpResponseForbidden("Instructor role required")

    courses = (
        Course.objects.filter(instructor=user)
        .annotate(student_count=Count("enrollments"))
        .order_by("-created_at")
    )
    return render(request, "courses/courses-instructor.html", {"courses": courses})


class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    model = Course
    fields = ["title", "course_code", "description", "credit_points", "status"]
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("instructor_courses")

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)


@login_required
def course_delete(request, pk: int):
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    if request.method == "POST":
        title = course.title
        course.delete()
        messages.success(request, f"Deleted course '{title}'.")
        return redirect("instructor_courses")
    return HttpResponseForbidden("Deletion requires POST")
