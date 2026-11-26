from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import AttendanceRecord


@login_required
def attendance_list(request):
    records = AttendanceRecord.objects.select_related('course', 'student').order_by('-date')[:100]
    return render(request, 'attendance/attendance_list.html', {'records': records})
