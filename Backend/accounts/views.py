from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.shortcuts import render, redirect, resolve_url, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required,user_passes_test
from django.utils.decorators import method_decorator
from .forms import InstructorCreationForm, InstructorChangeForm, AdminLoginForm
from .forms import StudentSignupForm
from .models import User
from django.contrib.auth import logout as auth_logout
from django.contrib import messages as dj_messages
from django.db.models import Count
from django.views.decorators.http import require_POST

class RoleSelectView(TemplateView):
    template_name = "accounts/role_select.html"

class StudentSignupView(View):
    def get(self, request):
        form = StudentSignupForm()
        return render(
            request,
            "accounts/student_login.html",
            {"signup_form": form, "role": "Student", "show_signup": True, "open_register": True},
        )

    def post(self, request):
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Add to Student group if available
            try:
                student_group = Group.objects.get(name="Student")
                user.groups.add(student_group)
            except Group.DoesNotExist:
                pass

            messages.success(request, "Account created. Please log in.")
            return redirect("login_student")
        return render(
            request,
            "accounts/student_login.html",
            {"signup_form": form, "role": "Student", "show_signup": True, "open_register": True},
        )

class LoginStudentView(LoginView):
    template_name = "accounts/student_login.html"
    extra_context = {"role": "Student", "show_signup": True, "open_register": False}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("signup_form", StudentSignupForm())
        return ctx

    def get_success_url(self):
        return reverse("student_dashboard")

class LoginInstructorView(LoginView):
    template_name = "accounts/instructor_login.html"
    extra_context = {"role": "Instructor", "show_signup": False}

    def get_success_url(self):
        return reverse("instructor_dashboard")

def is_admin(user):
    return user.is_authenticated and user.role == User.Roles.ADMIN

def is_student(user):
    return user.is_authenticated and user.role == User.Roles.STUDENT

def admin_login(request):

    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)

            if user is not None and getattr(user, "role", None) == User.Roles.ADMIN:
                auth_login(request, user)
                messages.success(request, "Welcome, Admin!")
                return redirect("admin_dashboard")
            else:
                messages.error(request, "Invalid credentials or not an admin.")
    else:
        form = AdminLoginForm()
    return render(request, "accounts/admin_login.html", {"form": form})

@login_required
@user_passes_test(lambda u: getattr(u, "role", None) == User.Roles.ADMIN)
def admin_dashboard(request):
    ctx = {
        "form": InstructorCreationForm(),
        "show_instructor_form": False,
    }
    return render(request, "accounts/admin-menu.html", ctx)

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    return render(request, "accounts/student-menu.html")

def logout_view(request):
    """Custom logout that allows GET and POST, then redirects to role select."""
    auth_logout(request)
    # Clear any queued messages so they don't appear after logout
    storage = dj_messages.get_messages(request)
    for _ in storage:
        pass
    storage.used = True
    return redirect("role_select")

@login_required
@user_passes_test(is_admin)
def create_instructor(request):
    if request.method == "POST":
        form = InstructorCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Instructor account created successfully.")
            return redirect("admin_dashboard")
        # If coming from embedded form on dashboard, re-render dashboard with errors
        if request.POST.get("from_dashboard"):
            return render(
                request,
                "accounts/admin-menu.html",
                {"form": form, "show_instructor_form": True},
            )
    else:
        form = InstructorCreationForm()

    return render(request, "accounts/create_instructor.html", {"form": form})

@login_required
@user_passes_test(is_admin)
def edit_instructor(request, instructor_id):
    instructor = get_object_or_404(User, id=instructor_id, role=User.Roles.INSTRUCTOR)

    if request.method == "POST":
        form = InstructorChangeForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, "Instructor updated successfully.")
            return redirect("admin_dashboard")
    else:
        form = InstructorChangeForm(instance=instructor)

    return render(request, "accounts/edit_instructor.html", {"form": form, "instructor": instructor})


@login_required
@user_passes_test(is_admin)
def manage_instructors(request):
    instructors = (
        User.objects.filter(role=User.Roles.INSTRUCTOR)
        .annotate(course_count=Count("courses"))
        .order_by("id")
    )
    return render(request, "accounts/manage_instructor.html", {"instructors": instructors})


@login_required
@user_passes_test(is_admin)
@require_POST
def set_instructor_status(request, instructor_id: int):
    instructor = get_object_or_404(User, id=instructor_id, role=User.Roles.INSTRUCTOR)
    action = request.POST.get("action")
    if action == "activate":
        instructor.is_active = True
        instructor.save(update_fields=["is_active"])
        messages.success(request, f"Activated {instructor.get_full_name() or instructor.email}.")
    elif action == "deactivate":
        instructor.is_active = False
        instructor.save(update_fields=["is_active"])
        messages.success(request, f"Deactivated {instructor.get_full_name() or instructor.email}.")
    else:
        messages.error(request, "Invalid action.")
    return redirect("manage_instructors")

@login_required
def instructor_dashboard(request):
    if getattr(request.user, "role", None) != User.Roles.INSTRUCTOR:
        messages.error(request, "Access denied. Instructors only.")
        return redirect("role_select")
    return render(request, "accounts/instructor-menu.html")

@login_required
def instructor_courses(request):
    if getattr(request.user, "role", None) != User.Roles.INSTRUCTOR:
        messages.error(request, "Access denied. Instructors only.")
        return redirect("role_select")

    return render(request, "courses/courses-instructor.html")
