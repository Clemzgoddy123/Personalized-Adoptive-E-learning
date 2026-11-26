from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_dashboard, name='student_dashboard'),
    path('videos/<int:material_id>/complete/', views.mark_video_complete, name='mark_video_complete'),
]
