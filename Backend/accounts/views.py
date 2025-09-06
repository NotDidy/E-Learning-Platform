from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.shortcuts import render, redirect, resolve_url
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from .forms import StudentSignupForm


class RoleSelectView(TemplateView):
    template_name = "accounts/role_select.html"


class StudentSignupView(View):
    def get(self, request):
        form = StudentSignupForm()
        return render(
            request,
            "accounts/login_student.html",
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

            # Try to authenticate and log in the user immediately
            raw_password = form.cleaned_data.get("password1")
            authed = None
            if raw_password:
                authed = authenticate(request, username=user.username, password=raw_password)
            if authed is not None:
                auth_login(request, authed)
                messages.success(request, "Welcome! Your student account is ready.")
                return redirect(resolve_url(getattr(settings, "LOGIN_REDIRECT_URL", "/")))

            messages.success(request, "Account created. Please log in.")
            return redirect(resolve_url(getattr(settings, "LOGIN_URL", "login")))
        return render(
            request,
            "accounts/login_student.html",
            {"signup_form": form, "role": "Student", "show_signup": True, "open_register": True},
        )


class LMSLoginView(LoginView):
    template_name = "accounts/login.html"


class LoginStudentView(LMSLoginView):
    template_name = "accounts/login_student.html"
    extra_context = {"role": "Student", "show_signup": True}
