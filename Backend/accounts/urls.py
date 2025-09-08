from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from .views import (
    LoginStudentView,
    LoginInstructorView,
    RoleSelectView,
    StudentSignupView,
)

urlpatterns = [
    path("", RoleSelectView.as_view(), name="role_select"),
    path("login/student/", LoginStudentView.as_view(), name="login_student"),
    path("signup/student/", StudentSignupView.as_view(), name="signup_student"),
    path("login/instructor/", LoginInstructorView.as_view(), name="login_instructor"),
    path("logout/", LogoutView.as_view(next_page="role_select"), name="logout"),
    path("admin/login/", views.admin_login, name="login_admin"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/create-instructor/", views.create_instructor, name="create_instructor"),
    path("admin/edit-instructor/<int:instructor_id>/", views.edit_instructor, name="edit_instructor"),
]
