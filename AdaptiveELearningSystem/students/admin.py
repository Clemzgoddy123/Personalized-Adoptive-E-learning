from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'class_level', 'guardian_contact', 'enrolled_at')
    search_fields = ('user__username', 'user__email', 'class_level')
    list_filter = ('class_level',)
