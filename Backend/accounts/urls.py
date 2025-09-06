from django.urls import path

from .views import (
    LMSLoginView,
    LoginStudentView,
    RoleSelectView,
    StudentSignupView,
)

# Note: We won't include this directly; lms/urls.py will map names to keep namespace 'lms'

urlpatterns = [
    path("", RoleSelectView.as_view(), name="role_select"),
    path("login/", LMSLoginView.as_view(), name="login"),
    path("login/student/", LoginStudentView.as_view(), name="login_student"),
    path("signup/student/", StudentSignupView.as_view(), name="signup_student"),
]