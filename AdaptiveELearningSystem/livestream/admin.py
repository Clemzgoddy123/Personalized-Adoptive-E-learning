from django.contrib import admin
from .models import LiveClass


@admin.register(LiveClass)
class LiveClassAdmin(admin.ModelAdmin):
    list_display = ('course', 'teacher', 'scheduled_time', 'status')
    search_fields = ('course__title', 'teacher__user__username')
    list_filter = ('status',)
