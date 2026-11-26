from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Notification


@login_required
def notification_list(request):
    # mark unread notifications as read when listing
    Notification.objects.filter(user=request.user, read_status=False).update(read_status=True)
    notifications = Notification.objects.filter(user=request.user).order_by('-date_sent')
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})
