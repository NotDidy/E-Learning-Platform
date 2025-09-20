from django.urls import path
from . import views


urlpatterns = [
    path("", views.classrooms, name="classrooms"),
    path("create/", views.create_classroom, name="create_classroom"),
    path('classrooms/<int:classroom_id>/preview/', views.classroom_preview, name='classroom_preview'),
]