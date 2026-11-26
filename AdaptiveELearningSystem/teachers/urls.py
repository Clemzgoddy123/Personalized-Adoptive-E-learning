from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_dashboard, name='teacher_dashboard'),
    path('students/', views.view_student, name='view_student'),
    path('students/course/<int:course_id>/', views.view_student, name='view_students_by_course'),
    path('materials/upload/', views.upload_learning_material, name='upload_learning_material'),
    path('materials/<int:material_id>/delete/', views.delete_learning_material, name='delete_learning_material'),
]
