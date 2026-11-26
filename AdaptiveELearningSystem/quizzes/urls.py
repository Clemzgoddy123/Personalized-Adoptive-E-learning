from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz_list, name='quiz_list'),
    path('create/', views.teacher_quiz_create, name='teacher_quiz_create'),
    path('take/<int:quiz_id>/', views.student_take_quiz, name='student_take_quiz'),
    path('view/<int:quiz_id>/', views.student_view_quiz_questions, name='student_view_quiz_questions'),
]
