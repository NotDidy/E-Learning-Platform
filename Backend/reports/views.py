from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from accounts.models import User
from courses.models import Course, Enrollment, LessonProgress, CreditTransaction

@login_required
def instructor_report_list(request):
    """
     Shows a list of all students enrolled in the instructor’s courses with their progress summary.
    """
    user = request.user
    if getattr(user, "role", None) != User.Roles.INSTRUCTOR:
        return HttpResponseForbidden("Instructor access required")

    courses = Course.objects.filter(instructor=user).prefetch_related("enrollments__student")
    students = []

    for course in courses:
        for enrollment in course.enrollments.all():
            student = enrollment.student
            lessons_total = course.lessons.count()
            completed_count = LessonProgress.objects.filter(
                student=student, lesson__course=course, completed=True
            ).count()
            percent = round((completed_count / lessons_total) * 100) if lessons_total else 0
            students.append({
                "id": student.id,
                "name": student.get_full_name() or student.email,
                "email": student.email,
                "student_id": getattr(student, "student_id", ""),
                "initials": (student.get_full_name()[:2] if student.get_full_name() else student.email[:2]).upper(),
                "completed_lessons": completed_count,
                "overall_percent": percent,
                "active_classrooms": course.classrooms.count(),
                "course_id": course.id,
            })

    context = {"students": students}
    return render(request, "reports/instructor_report_list.html", context)

@login_required
def student_course_report(request, course_id: int, student_id: int):
    course = get_object_or_404(Course, pk=course_id)
    student = get_object_or_404(User, pk=student_id)

    user = request.user
    try:
        is_instructor = getattr(user, "role", None) == user.__class__.Roles.INSTRUCTOR  # type: ignore[attr-defined]
    except Exception:
        is_instructor = False

    if not is_instructor or course.instructor_id != user.id:
        return HttpResponseForbidden("Instructor access required")

    if student.role != User.Roles.STUDENT:
        return HttpResponseForbidden("Only student reports are available")

    enrollment = get_object_or_404(Enrollment, course=course, student=student)

    classrooms = (
        course.classrooms.select_related("supervisor")
        .prefetch_related("schedules")
        .annotate(schedule_count=Count("schedules", distinct=True))
        .order_by("name")
    )

    completed_lessons_qs = (
        LessonProgress.objects.filter(
            student=student,
            lesson__course=course,
            completed=True,
        )
        .select_related("lesson")
        .order_by("-updated_at")
    )

    lessons_total = course.lessons.count()
    completed_lessons_count = completed_lessons_qs.count()
    completion_percent = (
        round((completed_lessons_count / lessons_total) * 100)
        if lessons_total
        else 0
    )

    credits_total = (
        CreditTransaction.objects.filter(
            student=student,
            lesson__course=course,
        ).aggregate(total=Coalesce(Sum("credits"), 0))
    )["total"]

    completed_lessons = []
    for progress in completed_lessons_qs:
        lesson = progress.lesson
        lesson_code = lesson.lesson_code or f"L{lesson.id:03d}"
        completed_lessons.append(
            {
                "code": lesson_code,
                "title": lesson.title,
                "completed_on": progress.updated_at,
            }
        )

    classroom_cards = []
    for classroom in classrooms:
        schedules = []
        for schedule in classroom.schedules.all():
            day_label = schedule.get_day_display()
            day_short = day_label[:3] if day_label else schedule.day.title()
            schedules.append(
                f"{day_short} {schedule.start_time.strftime('%H:%M')} - {schedule.end_time.strftime('%H:%M')}"
            )

        if schedules:
            schedule_label = schedules[0]
            if len(schedules) > 1:
                schedule_label = f"{schedule_label} (+{len(schedules) - 1} more)"
        else:
            schedule_label = "Schedule not set"

        classroom_cards.append(
            {
                "name": classroom.name,
                "code": classroom.class_code,
                "schedule": schedule_label,
                "supervisor": classroom.supervisor,
            }
        )

    progress = {
        "lessons_total": lessons_total,
        "completed_lessons": completed_lessons_count,
        "completion_percent": completion_percent,
        "active_classrooms": classrooms.count(),
        "students_total": course.enrollments.count(),
        "credits_earned": credits_total,
        "remaining_lessons": max(lessons_total - completed_lessons_count, 0),
        "completed_lessons_percent": completion_percent,
        "overall_percent": completion_percent,
    }

    context = {
        "course": course,
        "student": student,
        "enrollment": enrollment,
        "classrooms": classrooms,
        "progress_available": lessons_total > 0,
        "progress": progress,
        "completed_lessons": completed_lessons,
        "classroom_cards": classroom_cards,
    }

    return render(request, "reports/student_report.html", context)
