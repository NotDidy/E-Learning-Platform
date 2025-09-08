from django.urls import path
from . import views
from .views import (
    LoginStudentView,
    RoleSelectView,
    StudentSignupView,
)

urlpatterns = [
    path("", RoleSelectView.as_view(), name="role_select"),
    path("login/student/", LoginStudentView.as_view(), name="login_student"),
    path("login/student/", StudentSignupView.as_view(), name="signup_student"),
    path("admin/login/", views.admin_login, name="admin_login"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/create-instructor/", views.create_instructor, name="create_instructor"),
]