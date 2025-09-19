from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from django.contrib import messages
from .models import Classroom, Schedule
from .forms import ClassroomForm, ScheduleForm
from django.contrib.auth.decorators import login_required, user_passes_test

def is_instructor(user):
    return user.is_authenticated and user.role == user.Roles.INSTRUCTOR


def classrooms(request):
    classrooms = Classroom.objects.all()
    return render(request, "classrooms/classrooms.html", {"classrooms": classrooms})

@login_required
@user_passes_test(is_instructor)
def create_classroom(request):
    ScheduleFormSet = modelformset_factory(Schedule, form=ScheduleForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = ClassroomForm(request.POST)
        formset = ScheduleFormSet(request.POST, queryset=Schedule.objects.none())

        if form.is_valid() and formset.is_valid():
            classroom = form.save()

            schedules = formset.save(commit=False)
            for schedule in schedules:
                schedule.classroom = classroom
                schedule.save()

            messages.success(request, "Classroom created successfully!")
            return redirect("classrooms")

    else:
        form = ClassroomForm()
        formset = ScheduleFormSet(queryset=Schedule.objects.none())

    return render(request, "classrooms/create_classrooms.html", {"form": form, "formset": formset})