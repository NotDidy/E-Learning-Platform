from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from accounts.models import User
from courses.models import Course, Enrollment


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
        .annotate(schedule_count=Count("schedules", distinct=True))
        .order_by("name")
    )

    stats = {
        "lessons_total": course.lessons.count(),
        "classrooms_total": classrooms.count(),
        "students_total": course.enrollments.count(),
    }

    context = {
        "course": course,
        "student": student,
        "enrollment": enrollment,
        "classrooms": classrooms,
        "stats": stats,
        "progress_available": False,
    }

    return render(request, "reports/student_report.html", context)
