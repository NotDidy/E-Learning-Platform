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
            return redirect(resolve_url(getattr(settings, "LOGIN_URL", "login")))
        return render(
            request,
            "accounts/student_login.html",
            {"signup_form": form, "role": "Student", "show_signup": True, "open_register": True},
        )

class LoginStudentView(LoginView):
    template_name = "accounts/student_login.html"
    extra_context = {"role": "Student", "show_signup": True, "open_register": False}
    #redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Provide signup form so the template can render both panes
        ctx.setdefault("signup_form", StudentSignupForm())
        return ctx


def admin_login(request):

    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)

            if user is not None and user.is_staff:
                auth_login(request, user)
                messages.success(request, "Welcome, Admin!")
                return redirect("admin_dashboard")
            else:
                messages.error(request, "Invalid credentials or not an admin.")
    else:
        form = AdminLoginForm()
    return render(request, "accounts/admin_login.html", {"form": form})

@login_required
def admin_dashboard(request):
    return render(request, "accounts/admin_dashboard.html")

#Only allow Admins
def is_admin(user):
    return user.is_authenticated and user.role == User.Roles.ADMIN

@login_required
@user_passes_test(is_admin)
def create_instructor(request):
    if request.method == "POST":
        form = InstructorCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Instructor account created successfully.")
            return redirect("admin_dashboard")
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
