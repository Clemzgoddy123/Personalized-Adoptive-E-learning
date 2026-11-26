import json

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from courses.models import Enrollment, LearningMaterial

from accounts.decorators import teacher_required
from .models import TeacherProfile
from assignments.models import Assignment, AssignmentSubmission
from attendance.models import AttendanceRecord
from livestream.models import LiveClass
from notifications.models import Notification
from quizzes.models import QuizResult
from recommendations.models import Recommendation
from .forms import LearningMaterialUploadForm


@teacher_required
def teacher_dashboard(request):
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    courses = teacher_profile.courses.all() if teacher_profile else []
    course_ids = [course.id for course in courses]
    now = timezone.now()

    course_count = courses.count() if teacher_profile else 0
    unique_student_count = Enrollment.objects.filter(course_id__in=course_ids).values('student_id').distinct().count() if course_ids else 0
    upcoming_assignments = Assignment.objects.filter(
        course_id__in=course_ids,
        deadline__gte=now
    ).select_related('course').order_by('deadline')[:6] if course_ids else []
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__course_id__in=course_ids,
        score__isnull=True
    ).select_related('assignment', 'student') if course_ids else []
    upcoming_live_classes = LiveClass.objects.filter(
        course_id__in=course_ids,
        scheduled_time__gte=now
    ).select_related('course').order_by('scheduled_time')[:6] if course_ids else []
    recent_attendance = AttendanceRecord.objects.filter(
        course_id__in=course_ids
    ).select_related('course', 'student').order_by('-date')[:6] if course_ids else []
    notifications = Notification.objects.filter(user=request.user).order_by('-date_sent')[:5] if teacher_profile else []
    unread_notifications = Notification.objects.filter(user=request.user, read_status=False).count() if teacher_profile else 0
    recommendations = Recommendation.get_recommendations_for_user(request.user) if teacher_profile else []

    course_metrics = []
    low_performing_students = []

    if course_ids:
        for course in courses:
            assignment_submissions = AssignmentSubmission.objects.filter(
                assignment__course=course,
                score__isnull=False
            ).select_related('assignment', 'student')
            quiz_results = QuizResult.objects.filter(
                quiz__course=course
            ).select_related('quiz', 'student')
            attendance_records = AttendanceRecord.objects.filter(course=course)

            assignment_average = None
            if assignment_submissions.exists():
                total_percent = 0
                for submission in assignment_submissions:
                    total_percent += float(submission.score) / submission.assignment.max_score * 100
                assignment_average = int(total_percent / assignment_submissions.count())

            quiz_average = None
            if quiz_results.exists():
                total_percent = 0
                for result in quiz_results:
                    total_percent += float(result.score) / result.quiz.total_marks * 100
                quiz_average = int(total_percent / quiz_results.count())

            attendance_rate = None
            if attendance_records.exists():
                present_count = attendance_records.filter(status='present').count()
                attendance_rate = int(present_count / attendance_records.count() * 100)

            course_metrics.append({
                'course': course,
                'assignment_average': assignment_average,
                'quiz_average': quiz_average,
                'attendance_rate': attendance_rate,
            })

        student_stats = {}
        student_submissions = AssignmentSubmission.objects.filter(
            assignment__course_id__in=course_ids,
            score__isnull=False
        ).select_related('student', 'assignment')

        for submission in student_submissions:
            student_id = submission.student_id
            percent = float(submission.score) / submission.assignment.max_score * 100
            if student_id not in student_stats:
                student_stats[student_id] = {
                    'student': submission.student,
                    'total_percent': 0,
                    'count': 0,
                }
            student_stats[student_id]['total_percent'] += percent
            student_stats[student_id]['count'] += 1

        for stats in student_stats.values():
            if stats['count'] > 0:
                avg_percent = int(stats['total_percent'] / stats['count'])
                if avg_percent < 60:
                    low_performing_students.append({
                        'student': stats['student'],
                        'average_percent': avg_percent,
                    })

        low_performing_students.sort(key=lambda item: item['average_percent'])
        low_performing_students = low_performing_students[:5]

    course_labels = [metric['course'].title for metric in course_metrics]
    teacher_assignment_averages = [metric['assignment_average'] if metric['assignment_average'] is not None else 0 for metric in course_metrics]
    teacher_quiz_averages = [metric['quiz_average'] if metric['quiz_average'] is not None else 0 for metric in course_metrics]
    teacher_attendance_rates = [metric['attendance_rate'] if metric['attendance_rate'] is not None else 0 for metric in course_metrics]

    teacher_course_chart = {
        'labels': json.dumps(course_labels),
        'assignment_averages': json.dumps(teacher_assignment_averages),
        'quiz_averages': json.dumps(teacher_quiz_averages),
        'attendance_rates': json.dumps(teacher_attendance_rates),
    }
    teacher_course_chart_available = bool(course_metrics)

    teacher_performance_chart = {
        'labels': json.dumps(['Assignment Avg', 'Quiz Avg', 'Attendance Rate']),
        'values': json.dumps([
            int(sum(teacher_assignment_averages) / len(teacher_assignment_averages)) if teacher_assignment_averages else 0,
            int(sum(teacher_quiz_averages) / len(teacher_quiz_averages)) if teacher_quiz_averages else 0,
            int(sum(teacher_attendance_rates) / len(teacher_attendance_rates)) if teacher_attendance_rates else 0,
        ]),
    }

    teacher_assignment_performance_chart = {
        'labels': json.dumps(course_labels),
        'values': json.dumps(teacher_assignment_averages),
    }

    teacher_quiz_performance_chart = {
        'labels': json.dumps(course_labels),
        'values': json.dumps(teacher_quiz_averages),
    }

    attendance_history = list(recent_attendance)[::-1]
    teacher_attendance_trend = {
        'labels': json.dumps([record.date.strftime('%Y-%m-%d') for record in attendance_history]),
        'scores': json.dumps([
            100 if record.status == 'present' else 60 if record.status == 'late' else 0
            for record in attendance_history
        ]),
    }

    total_assignments = Assignment.objects.filter(course_id__in=course_ids).count() if course_ids else 0
    graded_assignments = AssignmentSubmission.objects.filter(
        assignment__course_id__in=course_ids,
        score__isnull=False
    ).count() if course_ids else 0
    teacher_course_completion_rate = int(graded_assignments / total_assignments * 100) if total_assignments else 0

    uploaded_learning_materials = list(
        LearningMaterial.objects.filter(course_id__in=course_ids)
        .select_related('course')
        .order_by('-upload_date')[:10]
    ) if course_ids else []

    video_completion_stats = []
    for material in uploaded_learning_materials:
        if material.material_type == 'video':
            completed_count = material.watch_progress.filter(watched_complete=True).count()
            total_students = Enrollment.objects.filter(course=material.course).count()
            percent_complete = int((completed_count / total_students) * 100) if total_students else 0
            video_completion_stats.append({
                'material': material,
                'completed_count': completed_count,
                'total_students': total_students,
                'percent_complete': percent_complete,
            })

    return render(request, 'teachers/teacher_dashboard.html', {
        'teacher_profile': teacher_profile,
        'courses': courses,
        'course_count': course_count,
        'unique_student_count': unique_student_count,
        'upcoming_assignments': upcoming_assignments,
        'pending_submissions': pending_submissions,
        'upcoming_live_classes': upcoming_live_classes,
        'recent_attendance': recent_attendance,
        'notifications': notifications,
        'unread_notifications': unread_notifications,
        'recommendations': recommendations,
        'course_metrics': course_metrics,
        'low_performing_students': low_performing_students,
        'teacher_course_chart': teacher_course_chart,
        'teacher_course_chart_available': teacher_course_chart_available,
        'teacher_performance_chart': teacher_performance_chart,
        'teacher_assignment_performance_chart': teacher_assignment_performance_chart,
        'teacher_quiz_performance_chart': teacher_quiz_performance_chart,
        'teacher_attendance_trend': teacher_attendance_trend,
        'teacher_course_completion_rate': teacher_course_completion_rate,
        'uploaded_learning_materials': uploaded_learning_materials,
        'video_completion_stats': video_completion_stats,
        'teacher_chart_data': {
            'course_labels': course_labels,
            'assignment_averages': teacher_assignment_averages,
            'quiz_averages': teacher_quiz_averages,
            'attendance_rates': teacher_attendance_rates,
            'completion_rate': teacher_course_completion_rate,
            'performance_labels': ['Assignment Avg', 'Quiz Avg', 'Attendance Rate'],
            'performance_values': [
                int(sum(teacher_assignment_averages) / len(teacher_assignment_averages)) if teacher_assignment_averages else 0,
                int(sum(teacher_quiz_averages) / len(teacher_quiz_averages)) if teacher_quiz_averages else 0,
                int(sum(teacher_attendance_rates) / len(teacher_attendance_rates)) if teacher_attendance_rates else 0,
            ],
            'attendance_labels': [record.date.strftime('%Y-%m-%d') for record in attendance_history],
            'attendance_scores': [
                100 if record.status == 'present' else 60 if record.status == 'late' else 0
                for record in attendance_history
            ],
        },
    })


@teacher_required
def upload_learning_material(request):
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    if teacher_profile is None:
        messages.error(request, 'A teacher profile is required to upload course materials.')
        return redirect('teacher_dashboard')

    initial_data = {}
    if request.GET.get('type') == 'video':
        initial_data['material_type'] = 'video'

    if request.method == 'POST':
        form = LearningMaterialUploadForm(
            request.POST,
            request.FILES,
            teacher_profile=teacher_profile,
            initial=initial_data,
        )
        if form.is_valid():
            material = form.save(commit=False)
            material.message_text = form.cleaned_data.get('message_text', '')
            material.save()
            material.refresh_from_db()

            message_text = form.cleaned_data.get('message_text', '').strip()
            if message_text:
                enrolled_students = Enrollment.objects.filter(course=material.course).select_related('student__user')
                for enrollment in enrolled_students:
                    Notification.objects.create(
                        user=enrollment.student.user,
                        message=f"New learning material: {material.title}. {message_text}",
                        notification_type='info',
                    )

            messages.success(request, f'{material.title} was uploaded successfully.')
            return redirect('teacher_dashboard')
    else:
        form = LearningMaterialUploadForm(teacher_profile=teacher_profile, initial=initial_data)

    return render(request, 'teachers/upload_material.html', {'form': form})


@teacher_required
def delete_learning_material(request, material_id):
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    if teacher_profile is None:
        return redirect('teacher_dashboard')

    material = LearningMaterial.objects.filter(id=material_id, course__teacher=teacher_profile).first()
    if material:
        material.delete()
        messages.success(request, 'The video was deleted successfully.')
    else:
        messages.error(request, 'You can only delete materials from your own courses.')

    return redirect('teacher_dashboard')


@teacher_required
def view_student(request, course_id=None):
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    if teacher_profile is None:
        messages.error(request, 'A teacher profile is required to view students.')
        return redirect('teacher_dashboard')

    courses = teacher_profile.courses.all().order_by('title')
    selected_course = None

    if course_id is not None:
        selected_course = courses.filter(id=course_id).first()
        if selected_course is None:
            messages.error(request, 'You can only view students enrolled in your own courses.')
            return redirect('view_student')

    if selected_course:
        enrollments = Enrollment.objects.filter(course=selected_course)
    else:
        enrollments = Enrollment.objects.filter(course__teacher=teacher_profile)

    enrollments = enrollments.select_related(
        'student', 'student__user', 'course'
    ).order_by('course__title', 'student__user__first_name', 'student__user__username')

    return render(request, 'teachers/view_students.html', {
        'teacher_profile': teacher_profile,
        'courses': courses,
        'selected_course': selected_course,
        'enrollments': enrollments,
    })
