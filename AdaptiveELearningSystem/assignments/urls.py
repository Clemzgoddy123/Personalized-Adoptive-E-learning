from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('create/', views.create_assignment, name='create_assignment'),
    path('<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('submission/<int:submission_id>/download-score/', views.download_submission_score, name='download_submission_score'),
]
