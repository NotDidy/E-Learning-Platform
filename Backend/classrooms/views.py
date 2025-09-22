from django.shortcuts import render, redirect, get_object_or_404
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
def classroom_preview(request, classroom_id):

    classroom = Classroom.objects.get(id=classroom_id)
    schedules = classroom.schedules.all()
    return render(request, "classrooms/classroom_preview.html", {"classroom": classroom, "schedules": schedules})

@login_required
@user_passes_test(is_instructor)
def create_classroom(request):
    ScheduleFormSet = modelformset_factory(Schedule, form=ScheduleForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = ClassroomForm(request.POST)
        form_valid = form.is_valid()
        classroom = form.save(commit=False) if form_valid else None
        formset = ScheduleFormSet(
            request.POST,
            queryset=Schedule.objects.none(),
            form_kwargs={"classroom": classroom},
        )

        if form_valid and formset.is_valid():
            classroom.save()
            schedules = formset.save(commit=False)
            for schedule in schedules:
                schedule.classroom = classroom
                schedule.save()
            formset.save_m2m()
            messages.success(request, "Classroom created successfully!")
            return redirect("classrooms")
    else:
        form = ClassroomForm()
        formset = ScheduleFormSet(
            queryset=Schedule.objects.none(),
            form_kwargs={"classroom": None},
        )

    return render(request, "classrooms/create_classrooms.html", {"form": form, "formset": formset})

@login_required
@user_passes_test(is_instructor)
def manage_classrooms_1(request, classroom_id):
    classroom = Classroom.objects.get(id=classroom_id)
    return render(
        request,
        "classrooms/manage_classrooms_1.html",
        {"classroom": classroom}
    )


@login_required
@user_passes_test(is_instructor)
def delete_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    if request.method == "POST":
        classroom.delete()
        return redirect("classrooms")
    return redirect("classrooms")