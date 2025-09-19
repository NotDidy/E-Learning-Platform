from django.urls import path
from . import views

urlpatterns = [
    path('courses/<int:course_id>/classrooms/', views.classroom_list, name='classroom_list'),
    path('courses/<int:course_id>/classrooms/create/', views.classroom_create, name='classroom_create'),
    path('classrooms/<int:classroom_id>/', views.classroom_detail, name='classroom_detail'),
    path('classrooms/<int:classroom_id>/add-student/', views.classroom_add_student, name='classroom_add_student'),
]