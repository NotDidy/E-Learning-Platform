from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from accounts.models import User
from courses.models import Course, Enrollment, LessonProgress, CreditTransaction

@login_required
def instructor_report_list(request):
    """Displays unique students under the instructor’s courses with aggregated progress."""
    instructor = request.user

    if getattr(instructor, "role", None) != User.Roles.INSTRUCTOR:
        return HttpResponseForbidden("Instructor access required")

    # Get all enrollments for this instructor’s courses
    enrollments = Enrollment.objects.filter(course__instructor=instructor).select_related("student", "course")


    students = (
        enrollments.values(
            "student__id",
            "student__first_name",
            "student__last_name",
            "student__email",
            "student__student_id",
        )
        .annotate(
            total_courses=Count("course", distinct=True),
            completed_lessons=Count(
                "student__lesson_progress",
                filter=Q(student__lesson_progress__completed=True),
                distinct=True,
            ),
            total_lessons=Count(
                "student__lesson_progress__lesson",
                distinct=True,
            ),
        )
        .order_by("student__last_name", "student__first_name")
        .distinct()
    )

    student_reports = []
    for s in students:
        total = s["total_lessons"]
        completed = s["completed_lessons"]
        percent = round((completed / total) * 100) if total else 0

        # Build initials for avatar
        first = (s["student__first_name"] or "").strip()
        last = (s["student__last_name"] or "").strip()
        initials = (first[:1] + last[:1]).upper() or (s["student__email"][:2].upper())
        first_course = (
            Enrollment.objects.filter(student_id=s["student__id"], course__instructor=instructor)
            .values_list("course_id", flat=True)
            .first()
        )

        student_reports.append({
            "id": s["student__id"],
            "first_name": s["student__first_name"],
            "last_name": s["student__last_name"],
            "email": s["student__email"],
            "student_id": s["student__student_id"],
            "initials": initials,
            "course_id": first_course,
            "total_courses": s["total_courses"],
            "completed_lessons": completed,
            "overall_percent": percent,
        })

    context = {"students": student_reports}
    return render(request, "reports/instructor_report_list.html", context)

@login_required
def student_course_report(request, course_id: int, student_id: int):
    course = get_object_or_404(Course, pk=course_id)
    student = get_object_or_404(User, pk=student_id)
    user = request.user

    # Determine roles
    user_role = getattr(user, "role", None)
    is_instructor = user_role == User.Roles.INSTRUCTOR
    is_student = user_role == User.Roles.STUDENT

    # Access control
    if is_instructor:
        if course.instructor_id != user.id:
            return HttpResponseForbidden("You can only view reports for your own courses.")
    elif is_student:
        if student.id != user.id:
            return HttpResponseForbidden("You can only view your own report.")
    else:
        return HttpResponseForbidden("Access denied.")

    if student.role != User.Roles.STUDENT:
        return HttpResponseForbidden("Only student reports are available.")

    # Ensure the student is enrolled
    enrollment = get_object_or_404(Enrollment, course=course, student=student)

    # Query data
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

    completed_lessons = [
        {
            "code": lp.lesson.lesson_code or f"L{lp.lesson.id:03d}",
            "title": lp.lesson.title,
            "completed_on": lp.updated_at,
        }
        for lp in completed_lessons_qs
    ]

    classroom_cards = []
    for classroom in classrooms:
        schedules = [
            f"{s.get_day_display()[:3]} {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
            for s in classroom.schedules.all()
        ]
        schedule_label = schedules[0] if schedules else "Schedule not set"
        if len(schedules) > 1:
            schedule_label = f"{schedule_label} (+{len(schedules) - 1} more)"
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
