from .models import Notification


def unread_notifications_count(request):
    if request.user.is_authenticated:
        try:
            return {'unread_notifications_count': Notification.objects.filter(user=request.user, read_status=False).count()}
        except Exception:
            return {'unread_notifications_count': 0}
    return {'unread_notifications_count': 0}
