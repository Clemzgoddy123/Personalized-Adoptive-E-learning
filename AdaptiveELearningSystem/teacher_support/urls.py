from django.urls import path
from . import views

app_name = 'teacher_support'

urlpatterns = [
    path('', views.decision_support, name='decision_support'),
]
