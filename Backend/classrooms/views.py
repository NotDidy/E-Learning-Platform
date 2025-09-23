from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ClassroomForm, ScheduleForm
from .models import Classroom, Schedule


def is_instructor(user):
    return user.is_authenticated and user.role == user.Roles.INSTRUCTOR


def classrooms(request):
    classrooms = Classroom.objects.all()
    return render(request, "classrooms/classrooms.html", {"classrooms": classrooms})


@login_required
def classroom_preview(request, classroom_id):
    classroom = Classroom.objects.get(id=classroom_id)
    schedules = classroom.schedules.all()
    return render(
        request,
        "classrooms/classroom_preview.html",
        {"classroom": classroom, "schedules": schedules},
    )


@login_required
@user_passes_test(is_instructor)
def create_classroom(request):
    ScheduleFormSet = modelformset_factory(Schedule, form=ScheduleForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = ClassroomForm(request.POST)
        form_valid = form.is_valid()
        classroom_instance = form.save(commit=False) if form_valid else None
        formset = ScheduleFormSet(
            request.POST,
            queryset=Schedule.objects.none(),
            form_kwargs={"classroom": classroom_instance},
        )

        if form_valid and formset.is_valid():
            classroom = form.save()
            schedules = formset.save(commit=False)
            for schedule in schedules:
                schedule.classroom = classroom
                schedule.save()
            for schedule in formset.deleted_objects:
                schedule.delete()
            formset.save_m2m()
            messages.success(request, "Classroom created successfully!")
            return redirect("classrooms")
    else:
        form = ClassroomForm()
        formset = ScheduleFormSet(
            queryset=Schedule.objects.none(),
            form_kwargs={"classroom": None},
        )

    context = {
        "form": form,
        "formset": formset,
        "page_title": "Create New Classroom",
        "page_subtitle": "Fill in the details below to create a new classroom for your students",
        "submit_label": "Create Classroom",
        "submit_icon": "bx bx-check",
        "back_label": "Back to Classrooms",
        "cancel_label": "Cancel",
        "back_url": reverse("classrooms"),
        "cancel_url": reverse("classrooms"),
        "show_draft": True,
        "is_edit": False,
        "delete_url": None,
        "classroom": None,
    }
    return render(request, "classrooms/classroom_form.html", context)


@login_required
@user_passes_test(is_instructor)
def manage_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    ScheduleFormSet = modelformset_factory(Schedule, form=ScheduleForm, extra=1, can_delete=True)

    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=classroom)
        form_valid = form.is_valid()
        classroom_instance = form.save(commit=False) if form_valid else classroom
        formset = ScheduleFormSet(
            request.POST,
            queryset=classroom.schedules.all(),
            form_kwargs={"classroom": classroom_instance},
        )

        if form_valid and formset.is_valid():
            classroom = form.save()
            schedules = formset.save(commit=False)
            for schedule in schedules:
                schedule.classroom = classroom
                schedule.save()
            for schedule in formset.deleted_objects:
                schedule.delete()
            formset.save_m2m()
            messages.success(request, "Classroom updated successfully!")
            return redirect("classrooms")
    else:
        form = ClassroomForm(instance=classroom)
        formset = ScheduleFormSet(
            queryset=classroom.schedules.all(),
            form_kwargs={"classroom": classroom},
        )

    context = {
        "form": form,
        "formset": formset,
        "page_title": f"Edit {classroom.name}",
        "page_subtitle": "Update the classroom's details and schedule below.",
        "submit_label": "Save Changes",
        "submit_icon": "bx bx-save",
        "back_label": "Back to Classrooms",
        "cancel_label": "Discard Changes",
        "back_url": reverse("classrooms"),
        "cancel_url": reverse("classrooms"),
        "show_draft": False,
        "is_edit": True,
        "delete_url": reverse("delete_classroom", args=[classroom.id]),
        "classroom": classroom,
    }
    return render(request, "classrooms/classroom_form.html", context)


@login_required
@user_passes_test(is_instructor)
def delete_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    if request.method == "POST":
        classroom.delete()
        return redirect("classrooms")
    return redirect("classrooms")
