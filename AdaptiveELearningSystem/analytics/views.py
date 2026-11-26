from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from assignments.models import Assignment, AssignmentSubmission
from attendance.models import AttendanceRecord
from courses.models import Course
from livestream.models import LiveClass
from notifications.models import Notification
from quizzes.models import Quiz, QuizResult
from students.models import StudentProfile
from teachers.models import TeacherProfile


@login_required
def analytics_dashboard(request):
    upcoming_live_classes = LiveClass.objects.filter(scheduled_time__gte=timezone.now()).order_by('scheduled_time')[:5]
    recent_notifications = Notification.objects.order_by('-date_sent')[:5]

    context = {
        'total_courses': Course.objects.count(),
        'total_students': StudentProfile.objects.count(),
        'total_teachers': TeacherProfile.objects.count(),
        'total_assignments': Assignment.objects.count(),
        'total_submissions': AssignmentSubmission.objects.count(),
        'total_quizzes': Quiz.objects.count(),
        'total_quiz_results': QuizResult.objects.count(),
        'total_attendance_records': AttendanceRecord.objects.count(),
        'upcoming_live_classes': upcoming_live_classes,
        'recent_notifications': recent_notifications,
    }
    return render(request, 'analytics/analytics_dashboard.html', context)
