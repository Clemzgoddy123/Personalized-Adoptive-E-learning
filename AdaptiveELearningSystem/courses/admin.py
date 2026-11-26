from django.contrib import admin
from .models import Course, LearningMaterial, Enrollment, VideoWatchProgress


@admin.register(VideoWatchProgress)
class VideoWatchProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'material', 'watched_complete', 'updated_at')
    search_fields = ('student__user__username', 'material__title')
    list_filter = ('watched_complete',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'class_level', 'teacher', 'created_at')
    search_fields = ('title', 'subject', 'teacher__user__username')
    list_filter = ('subject', 'class_level')


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'material_type', 'upload_date')
    search_fields = ('title', 'course__title')
    list_filter = ('material_type',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_date')
    search_fields = ('student__user__username', 'course__title')
