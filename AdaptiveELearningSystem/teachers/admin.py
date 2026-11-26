from django.contrib import admin
from .models import TeacherProfile


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject_specialization', 'qualification', 'created_at')
    search_fields = ('user__username', 'user__email', 'subject_specialization')
    list_filter = ('subject_specialization',)
