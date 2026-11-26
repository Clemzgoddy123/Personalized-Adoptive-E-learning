import json
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.decorators import student_required
from .models import StudentProfile
from assignments.models import Assignment, AssignmentSubmission
from attendance.models import AttendanceRecord
from livestream.models import LiveClass
from notifications.models import Notification
from quizzes.models import QuizResult
from recommendations.models import Recommendation
from courses.models import LearningMaterial, VideoWatchProgress


def _safe_percentage(value, total):
    if total in (None, 0):
        return 0
    try:
        return int((Decimal(value) / Decimal(total)) * Decimal('100'))
    except (InvalidOperation, TypeError, ValueError, ZeroDivisionError):
        return 0


@student_required
def mark_video_complete(request, material_id):
    material = LearningMaterial.objects.filter(id=material_id, material_type='video').first()
    if not material:
        return render(request, 'students/student_dashboard.html', {'student_profile': None})

    student_profile = StudentProfile.objects.filter(user=request.user).first()
    if student_profile:
        progress, _ = VideoWatchProgress.objects.get_or_create(material=material, student=student_profile)
        progress.watched_complete = True
        progress.save()

    return redirect('student_dashboard')


@student_required
def student_dashboard(request):
    student_profile = StudentProfile.objects.filter(user=request.user).select_related('user').first()
    enrollments = student_profile.enrollments.select_related('course') if student_profile else []
    course_ids = [enrollment.course.id for enrollment in enrollments]
    now = timezone.now()
    upcoming_assignments = []
    submitted_assignment_ids = []
    recent_quiz_results = []
    recent_attendance = []
    upcoming_live_classes = []

    notifications = []
    unread_notifications = 0
    attendance_summary = {
        'present': 0,
        'absent': 0,
        'late': 0,
        'total': 0,
    }
    assignment_progress = {
        'completed': 0,
        'pending': 0,
        'total': 0,
        'percent': 0,
    }
    quiz_progress = []
    performance_metrics = {
        'average_assignment_percent': None,
        'average_quiz_percent': None,
        'overall_percent': None,
        'attendance_rate': None,
        'message': None,
    }
    course_performance = []
    latest_feedback = []
    course_completion_rate = 0
    learning_materials = []
    student_assignment_trend = {'labels': [], 'scores': []}
    student_quiz_trend = {'labels': [], 'scores': []}
    has_assignment_trend = False
    has_quiz_trend = False
    recommendations = Recommendation.get_recommendations_for_user(request.user) if student_profile else []

    if student_profile:
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-date_sent')[:5]
        unread_notifications = Notification.objects.filter(
            user=request.user,
            read_status=False,
        ).count()

        if course_ids:
            upcoming_assignments = Assignment.objects.filter(
                course_id__in=course_ids,
                deadline__gte=now
            ).select_related('course').order_by('deadline')[:6]

            submitted_assignment_ids = list(AssignmentSubmission.objects.filter(
                student=student_profile,
                assignment__in=upcoming_assignments
            ).values_list('assignment_id', flat=True))

            assignment_progress['total'] = upcoming_assignments.count()
            assignment_progress['completed'] = len(submitted_assignment_ids)
            assignment_progress['pending'] = assignment_progress['total'] - assignment_progress['completed']
            assignment_progress['percent'] = _safe_percentage(assignment_progress['completed'], assignment_progress['total'])

            total_course_assignments = Assignment.objects.filter(course_id__in=course_ids).count()
            completed_course_assignments = AssignmentSubmission.objects.filter(
                student=student_profile,
                assignment__course_id__in=course_ids,
                score__isnull=False
            ).count()
            course_completion_rate = int(_safe_percentage(completed_course_assignments, total_course_assignments) or 0)

            upcoming_live_classes = LiveClass.objects.filter(
                course_id__in=course_ids,
                scheduled_time__gte=now
            ).select_related('course').order_by('scheduled_time')[:5]
        else:
            upcoming_assignments = []
            submitted_assignment_ids = []
            course_completion_rate = 0
            upcoming_live_classes = []

        graded_assignments = AssignmentSubmission.objects.filter(
            student=student_profile,
            score__isnull=False
        ).select_related('assignment').order_by('-submission_date')

        graded_assignment_data = []
        for submission in graded_assignments:
            percent = _safe_percentage(submission.score, submission.assignment.max_score)
            graded_assignment_data.append({
                'title': submission.assignment.title,
                'score': float(submission.score),
                'max_score': submission.assignment.max_score,
                'percent': percent,
                'feedback': submission.feedback,
                'date': submission.submission_date,
            })

        if graded_assignment_data:
            performance_metrics['average_assignment_percent'] = int(
                sum(item['percent'] for item in graded_assignment_data) / len(graded_assignment_data)
            )
            latest_feedback = [item for item in graded_assignment_data if item['feedback']][:3]

        assignment_trend_data = []
        if graded_assignment_data:
            assignment_trend_data = sorted(graded_assignment_data, key=lambda item: item['date'])[-6:]

        all_quiz_results = list(QuizResult.objects.filter(
            student=student_profile
        ).select_related('quiz__course'))

        quiz_trend_data = []
        if all_quiz_results:
            performance_metrics['average_quiz_percent'] = int(
                sum(_safe_percentage(result.score, result.quiz.total_marks) for result in all_quiz_results)
                / len(all_quiz_results)
            )
            quiz_trend_data = sorted(
                [
                    {
                        'label': result.quiz.title,
                        'percent': _safe_percentage(result.score, result.quiz.total_marks),
                        'date': result.date_taken,
                    }
                    for result in all_quiz_results
                ],
                key=lambda item: item['date']
            )[-6:]

        if performance_metrics['average_assignment_percent'] is None and performance_metrics['average_quiz_percent'] is None:
            performance_metrics['overall_percent'] = 0
        elif performance_metrics['average_assignment_percent'] is not None and performance_metrics['average_quiz_percent'] is not None:
            performance_metrics['overall_percent'] = int(
                (performance_metrics['average_assignment_percent'] + performance_metrics['average_quiz_percent']) / 2
            )
        else:
            performance_metrics['overall_percent'] = (performance_metrics['average_assignment_percent']
                if performance_metrics['average_assignment_percent'] is not None else performance_metrics['average_quiz_percent'])

        recent_quiz_results = QuizResult.objects.filter(
            student=student_profile
        ).select_related('quiz__course').order_by('-date_taken')[:5]

        quiz_progress = [
            {'quiz': result.quiz.title, 'course': result.quiz.course.title, 'score': result.score, 'max': result.quiz.total_marks}
            for result in recent_quiz_results
        ]

        recent_attendance = AttendanceRecord.objects.filter(
            student=student_profile
        ).select_related('course').order_by('-date')[:5]

        for record in recent_attendance:
            attendance_summary['total'] += 1
            if record.status in attendance_summary:
                attendance_summary[record.status] += 1
            else:
                attendance_summary['absent'] += 1

        if attendance_summary['total'] > 0:
            performance_metrics['attendance_rate'] = _safe_percentage(attendance_summary['present'], attendance_summary['total'])

        # Per-course performance for this student
        from courses.models import Course

        for enrollment in enrollments:
            course = enrollment.course
            assignment_submissions = AssignmentSubmission.objects.filter(
                student=student_profile,
                assignment__course=course,
                score__isnull=False
            ).select_related('assignment')
            quiz_results = QuizResult.objects.filter(
                student=student_profile,
                quiz__course=course
            ).select_related('quiz')
            attendance_records = AttendanceRecord.objects.filter(course=course, student=student_profile)

            assignment_average = None
            if assignment_submissions.exists():
                assignment_percentages = [
                    _safe_percentage(submission.score, submission.assignment.max_score)
                    for submission in assignment_submissions
                ]
                assignment_average = int(sum(assignment_percentages) / len(assignment_percentages))

            quiz_average = None
            if quiz_results.exists():
                quiz_percentages = [
                    _safe_percentage(result.score, result.quiz.total_marks)
                    for result in quiz_results
                ]
                quiz_average = int(sum(quiz_percentages) / len(quiz_percentages))

            attendance_rate = None
            if attendance_records.exists():
                present_count = attendance_records.filter(status='present').count()
                attendance_rate = _safe_percentage(present_count, attendance_records.count())

            course_performance.append({
                'course': course,
                'assignment_average': assignment_average,
                'quiz_average': quiz_average,
                'attendance_rate': attendance_rate,
            })

        learning_materials = list(
            LearningMaterial.objects.filter(course_id__in=course_ids)
            .select_related('course')
            .order_by('-upload_date')[:20]
        ) if course_ids else []

        for material in learning_materials:
            if material.material_type == 'video':
                material.user_completed = VideoWatchProgress.objects.filter(
                    material=material,
                    student=student_profile,
                    watched_complete=True,
                ).exists()

        student_assignment_trend = {
            'labels': [item['title'] for item in assignment_trend_data],
            'scores': [item['percent'] for item in assignment_trend_data],
        }
        has_assignment_trend = bool(assignment_trend_data)
        student_quiz_trend = {
            'labels': [item['label'] for item in quiz_trend_data],
            'scores': [item['percent'] for item in quiz_trend_data],
        }
        has_quiz_trend = bool(quiz_trend_data)

        student_performance_chart = {
            'labels': ['Assignment Avg', 'Quiz Avg', 'Attendance Rate'],
            'values': [
                performance_metrics['average_assignment_percent'] or 0,
                performance_metrics['average_quiz_percent'] or 0,
                performance_metrics['attendance_rate'] or 0,
            ],
        }

        attendance_records = AttendanceRecord.objects.filter(
            student=student_profile
        ).order_by('-date')[:10]
        attendance_history = list(attendance_records)[::-1]
        attendance_trend = {
            'labels': [record.date.strftime('%Y-%m-%d') for record in attendance_history],
            'scores': [
                100 if record.status == 'present' else 60 if record.status == 'late' else 0
                for record in attendance_history
            ],
        }
    else:
        student_performance_chart = {
            'labels': [],
            'values': [],
        }
        attendance_trend = {
            'labels': [],
            'scores': [],
        }
        course_completion_rate = 0

    assignment_progress_percent = assignment_progress.get('percent', 0)

    return render(request, 'students/student_dashboard.html', {
        'student_profile': student_profile,
        'enrollments': enrollments,
        'notifications': notifications,
        'assignment_progress': assignment_progress,
        'assignment_progress_percent': assignment_progress_percent,
        'attendance_summary': attendance_summary,
        'quiz_progress': quiz_progress,
        'upcoming_assignments': upcoming_assignments,
        'submitted_assignment_ids': submitted_assignment_ids,
        'recent_quiz_results': recent_quiz_results,
        'recent_attendance': recent_attendance,
        'upcoming_live_classes': upcoming_live_classes,
        'recommendations': recommendations,
        'unread_notifications': unread_notifications,
        'performance_metrics': performance_metrics,
        'course_performance': course_performance,
        'student_assignment_trend': student_assignment_trend,
        'student_quiz_trend': student_quiz_trend,
        'student_performance_chart': student_performance_chart,
        'attendance_trend': attendance_trend,
        'course_completion_rate': course_completion_rate,
        'latest_feedback': latest_feedback,
        'has_assignment_trend': has_assignment_trend,
        'has_quiz_trend': has_quiz_trend,
        'learning_materials': learning_materials,
    })
