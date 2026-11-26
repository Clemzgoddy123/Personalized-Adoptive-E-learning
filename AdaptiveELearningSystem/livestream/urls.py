from django.urls import path
from . import views

urlpatterns = [
    path('', views.live_class_list, name='live_class_list'),
    path('<int:live_class_id>/', views.live_class_detail, name='live_class_detail'),
    path('<int:live_class_id>/start/', views.start_live_class, name='start_live_class'),
    path('<int:live_class_id>/generate-link/', views.generate_new_jitsi_link, name='generate_new_jitsi_link'),
    path('<int:live_class_id>/cancel/', views.cancel_live_class, name='cancel_live_class'),
    path('<int:live_class_id>/end/', views.end_live_class, name='end_live_class'),
    path('<int:live_class_id>/delete/', views.delete_live_class, name='delete_live_class'),
]
