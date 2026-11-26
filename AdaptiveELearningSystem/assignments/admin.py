from django.contrib import admin
from .models import Assignment, AssignmentSubmission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline', 'max_score', 'created_at')
    search_fields = ('title', 'course__title')
    list_filter = ('course__subject',)


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submission_date', 'score')
    search_fields = ('assignment__title', 'student__user__username')
    list_filter = ('score',)
