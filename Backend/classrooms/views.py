from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import Classroom, ClassroomEnrollment
from courses.models import Course
from accounts.models import User

@login_required
def classroom_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    classrooms = course.classrooms.filter(instructor=request.user)
    return render(
        request,
        'classrooms/classroom_list.html',
        {'course': course, 'classrooms': classrooms}
    )

@login_required
def classroom_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        max_students = request.POST.get('max_students', 30)
        classroom = Classroom.objects.create(
            course=course,
            instructor=request.user,
            name=name,
            description=description,
            max_students=max_students
        )
        messages.success(request, f"Classroom '{classroom.name}' created.")
        return redirect('classroom_list', course_id=course.id)

    return render(request, 'classrooms/classroom_create.html', {'course': course})

@login_required
def classroom_detail(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, instructor=request.user)
    students = classroom.enrollments.select_related('student')
    return render(
        request,
        'classrooms/classroom_detail.html',
        {'classroom': classroom, 'students': students}
    )

@login_required
def classroom_add_student(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, instructor=request.user)
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student = get_object_or_404(User, id=student_id, role=User.Roles.STUDENT)
        ClassroomEnrollment.objects.get_or_create(classroom=classroom, student=student)
        messages.success(request, f"{student.email} added to {classroom.name}")
        return redirect('classroom_detail', classroom_id=classroom.id)

    # show list of students who are not yet enrolled
    enrolled_ids = classroom.enrollments.values_list('student_id', flat=True)
    available_students = User.objects.filter(role=User.Roles.STUDENT).exclude(id__in=enrolled_ids)
    return render(
        request,
        'classrooms/classroom_add_student.html',
        {'classroom': classroom, 'available_students': available_students}
    )