from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from django.db.models.functions import Coalesce
from django.db.models import F, Value
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import Course, Enrollment, Lesson, LessonProgress
from .forms import LessonForm

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
    fields = ["title", "course_code", "description", "status","duration_weeks", "max_students"]
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("instructor_courses")

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        messages.success(self.request, "Course created")
        return super().form_valid(form)

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/course_list.html"

    def get_queryset(self):
        user = self.request.user
        try:
            is_instructor = getattr(user, "role", None) == user.__class__.Roles.INSTRUCTOR 
        except Exception:
            is_instructor = False

        if is_instructor:
            return Course.objects.filter(instructor=user)
        else:
            return Course.objects.filter(status=Course.STATUS_ACTIVE)


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "courses/course_detail.html"

    def dispatch(self, request, *args, **kwargs):
        course = self.get_object()
        user = request.user

        try:
            is_instructor = getattr(user, "role", None) == user.__class__.Roles.INSTRUCTOR  # type: ignore[attr-defined]
        except Exception:
            is_instructor = False

        # Students cannot view drafts
        if not is_instructor and (course.status != Course.STATUS_ACTIVE):
            return HttpResponseForbidden("This course is not available")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course: Course = self.object
        ctx["lessons"] = course.lessons.all()
        user = self.request.user
        # Compute enrollment status for student users for template logic
        try:
            is_student = getattr(user, "role", None) == user.__class__.Roles.STUDENT  # type: ignore[attr-defined]
        except Exception:
            is_student = False
        ctx["is_student"] = is_student
        ctx["is_enrolled"] = False
        if is_student:
            ctx["is_enrolled"] = Enrollment.objects.filter(student=user, course=course).exists()

        enrollments = (
            course.enrollments.select_related("student")
            .order_by("student__first_name", "student__last_name", "student__email")
        )
        ctx["students"] = [enrollment.student for enrollment in enrollments]

        classrooms = (
            course.classrooms.annotate(schedule_count=Count("schedules", distinct=True))
            .select_related("supervisor")
            .order_by("name")
        )
        ctx["classrooms"] = classrooms
        return ctx

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
        Enrollment.objects.filter(student=user, course__status=Course.STATUS_ACTIVE)
        .select_related("course", "course__instructor")
        .prefetch_related("course__lessons")
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
        Course.objects.filter(status=Course.STATUS_ACTIVE)
        .exclude(id__in=enrolled_ids)
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
    """List courses owned by the logged-in instructor, with counts."""
    user = request.user

    # Simple role check
    try:
        is_instructor = getattr(user, "role", None) == user.__class__.Roles.INSTRUCTOR  # type: ignore[attr-defined]
    except Exception:
        is_instructor = False
    if not is_instructor:
        return HttpResponseForbidden("Instructor role required")

    # Fetch courses with student count, lesson count, and a placeholder for active classrooms
    courses = (
        Course.objects.filter(instructor=user)
        .annotate(
            student_count=Count("enrollments", distinct=True),
            lesson_count=Count("lessons", distinct=True),
            classroom_count=Count("classrooms", distinct=True),  
        )
        .prefetch_related("lessons", "enrollments__student")
        .order_by("-created_at")
    )

    return render(request, "courses/courses-instructor.html", {"courses": courses})


class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    model = Course
    fields = ["title", "course_code", "description", "status", "duration_weeks", "max_students"]
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


class LessonCreateView(InstructorRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = "courses/lesson_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=kwargs.get("course_id"), instructor=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["course"] = self.course
        return kwargs

    def form_valid(self, form):
        form.instance.course = self.course
        if not form.instance.instructor_id:
            form.instance.instructor = self.request.user or self.course.instructor
        messages.success(self.request, "Lesson created")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("lesson_detail", args=[self.object.id])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["course"] = self.course
        return ctx


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = "courses/lesson_detail.html"

    def dispatch(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, pk=kwargs.get("pk"))
        user = request.user
        # Allow course instructor
        if user.is_authenticated and lesson.course.instructor_id == user.id:
            self.object = lesson
            return super().dispatch(request, *args, **kwargs)
        # Allow enrolled students only
        try:
            is_student = getattr(user, "role", None) == user.__class__.Roles.STUDENT  # type: ignore[attr-defined]
        except Exception:
            is_student = False
        if is_student and Enrollment.objects.filter(student=user, course=lesson.course).exists():
            
            # Prerequisite enforcement via sections removed

            self.object = lesson
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden("Not allowed to view this lesson")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lesson: Lesson = self.object
        # sections removed
        # Split multi-line fields for styled lists
        def _split(text):
            return [line.strip() for line in (text or "").splitlines() if line.strip()]
        ctx["objectives_list"] = _split(lesson.learning_objectives)
        # Reading lines: best-effort link detection (http/https)
        readings = []
        for line in _split(lesson.reading_list):
            txt = line
            url = None
            idx_http = line.find('http://') if 'http://' in line else line.find('https://')
            if idx_http != -1:
                txt = line[:idx_http].strip() or line[idx_http:].strip()
                url = line[idx_http:].strip()
            readings.append({"text": txt, "url": url})
        ctx["reading_list"] = readings
        ctx["assignments_list"] = _split(getattr(lesson, "assignments", ""))
        # Publish status mirrors course state
        course = lesson.course
        course_published = (getattr(course, "status", None) == Course.STATUS_ACTIVE) and (not getattr(course, "is_draft", False))
        ctx["course_published"] = course_published
        ctx["course_status_label"] = "Published" if course_published else "Draft"
        schedules = (
            lesson.schedules.select_related("classroom")
            .order_by("classroom__name", "day", "start_time")
        )
        ctx["classroom_schedules"] = schedules
        
        ctx["materials"] = lesson.materials.all()

        user = self.request.user
        progress = None
        try:
            progress = LessonProgress.objects.get(student=user, lesson=lesson)
        except LessonProgress.DoesNotExist:
            progress = None
        ctx["lesson_progress"] = progress  

        total_lessons = lesson.course.lessons.count()
        completed_count = 0
        try:
            is_student = getattr(user, "role", None) == user.__class__.Roles.STUDENT
        except Exception:
            is_student = False
        if is_student:
            completed_count = LessonProgress.objects.filter(student=user, lesson__course=lesson.course, completed=True).count()
        ctx["course_total_lessons"] = total_lessons
        ctx["course_completed_lessons"] = completed_count
        ctx["course_percent_complete"] = round((completed_count / total_lessons * 100) if total_lessons else 0.0, 2)


        return ctx


class LessonUpdateView(InstructorRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = "courses/lesson_form.html"

    def get_queryset(self):
        return Lesson.objects.filter(course__instructor=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        obj = getattr(self, 'object', None)
        if obj:
            kwargs["course"] = obj.course
        return kwargs

    def form_valid(self, form):
        if not form.instance.instructor_id:
            form.instance.instructor = self.request.user
        messages.success(self.request, "Lesson updated")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("lesson_detail", args=[self.object.id])

@login_required
def lesson_delete(request, lesson_id: int):
    lesson = get_object_or_404(Lesson, pk=lesson_id, course__instructor=request.user)
    if request.method != "POST":
        return HttpResponseForbidden("Deletion requires POST")
    course_id = lesson.course_id
    title = lesson.title
    lesson.delete()
    messages.success(request, f"Deleted lesson '{title}'.")
    return redirect("course_detail", pk=course_id)

class CoursePreviewInstructorView(InstructorRequiredMixin, DetailView):
    model = Course
    template_name = "courses/course-details-instructor.html"
    context_object_name = "course"

    def get_queryset(self):
        # Instructors can only see their own courses
        return Course.objects.filter(instructor=self.request.user).prefetch_related("lessons")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course: Course = self.object

        ctx["lessons"] = course.lessons.all()
        ctx["students"] = [enrollment.student for enrollment in course.enrollments.select_related('student').all()]
        ctx["classrooms"] = course.classrooms.all()
        ctx["is_student"] = getattr(self.request.user, "role", None) == "STUDENT"
        ctx["is_enrolled"] = course.enrollments.filter(student=self.request.user).exists() if ctx["is_student"] else False

        return ctx
    
class CoursePreviewStudentView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "courses/course-details-student.html"
    context_object_name = "course"

    def dispatch(self, request, *args, **kwargs):
        course = self.get_object()
        user = request.user

        # Ensure only students can access
        try:
            is_student = getattr(user, "role", None) == user.__class__.Roles.STUDENT
        except Exception:
            is_student = False

        if not is_student:
            return HttpResponseForbidden("Student role required")

        # Students can view even if not enrolled
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course: Course = self.object
        user = self.request.user

        ctx["lessons"] = course.lessons.all()
        ctx["students"] = [enrollment.student for enrollment in course.enrollments.select_related("student").all()]
        ctx["classrooms"] = course.classrooms.all()
        ctx["is_student"] = True
        ctx["is_enrolled"] = Enrollment.objects.filter(student=user, course=course).exists()

        return ctx
    
@login_required
@require_POST
def toggle_lesson_progress(request, lesson_id):
    user = request.user
    lesson = get_object_or_404(Lesson, pk=lesson_id)

    try:
        is_student = getattr(user, "role", None) == user.__class__.Roles.STUDENT
    except Exception:
        is_student = False
    if not is_student:
        return JsonResponse({"error": "Only students may mark progress"}, status=403)

    if not Enrollment.objects.filter(student=user, course=lesson.course).exists():
        return JsonResponse({"error": "Student not enrolled in course"}, status=403)

    progress, created = LessonProgress.objects.get_or_create(student=user, lesson=lesson)
    progress.completed = not progress.completed
    progress.save()

    total_lessons = lesson.course.lessons.count() or 0
    completed_count = LessonProgress.objects.filter(
        student=user, lesson__course=lesson.course, completed=True
    ).count() if total_lessons > 0 else 0
    percent = (completed_count / total_lessons * 100) if total_lessons > 0 else 0.0

    return JsonResponse({
        "lesson_id": lesson.id,
        "completed": progress.completed,
        "completed_count": completed_count,
        "total_lessons": total_lessons,
        "percent_course_complete": round(percent, 2),
    })
