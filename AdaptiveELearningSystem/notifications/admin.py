from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'date_sent', 'read_status')
    search_fields = ('user__username', 'message')
    list_filter = ('notification_type', 'read_status')
