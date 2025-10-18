from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from accounts.models import User
from courses.models import Course, Enrollment, LessonProgress, CreditTransaction

@login_required
def instructor_report_list(request):
    """Show instructor overview of all students and their progress."""
    instructor = request.user
    try:
        is_instructor = getattr(instructor, "role", None) == instructor.__class__.Roles.INSTRUCTOR
    except Exception:
        is_instructor = False

    if not is_instructor:
        return HttpResponseForbidden("Instructor role required")

    courses = Course.objects.filter(instructor=instructor).prefetch_related("enrollments__student")

    course_reports = []
    all_students = set()
    total_progress_sum = 0
    total_students_count = 0

    for course in courses:
        students = []
        enrollments = Enrollment.objects.filter(course=course).select_related("student")

        for enrollment in enrollments:
            student = enrollment.student

            # Total credits earned by this student (sum across all lessons)
            total_credits = (
                CreditTransaction.objects.filter(student=student)
                .aggregate(total=Sum("credits"))["total"] or 0
            )

            # Compute overall progress out of 120 credits
            progress_percent = round((total_credits / 120) * 100, 1)
            total_progress_sum += progress_percent
            total_students_count += 1

            students.append({
                "id": student.id,
                "name": student.get_full_name() or student.email,
                "email": student.email,
                "credits": total_credits,
                "progress_percent": progress_percent,
            })

            all_students.add(student.id)

        course_reports.append({
            "course": course,
            "students": students
        })

    avg_progress = round(total_progress_sum / total_students_count, 1) if total_students_count else 0

    context = {
        "course_reports": course_reports,
        "summary": {
            "total_students": len(all_students),
            "courses_taught": courses.count(),
            "avg_progress": avg_progress,
        },
    }

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
