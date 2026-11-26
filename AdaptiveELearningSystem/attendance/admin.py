from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'date', 'status', 'recorded_at')
    search_fields = ('course__title', 'student__user__username')
    list_filter = ('status', 'date')
