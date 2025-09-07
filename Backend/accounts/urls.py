from django.urls import path
from . import views
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
    path("admin/login/", views.admin_login, name="admin_login"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/create-instructor/", views.create_instructor, name="create_instructor"),
]