from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import render

from assignments.models import Assignment, AssignmentSubmission
from attendance.models import AttendanceRecord
from courses.models import Course, Enrollment, VideoWatchProgress
from quizzes.models import QuizResult
from students.models import StudentProfile
from teachers.models import TeacherProfile


@login_required
def report_list(request):
    top_courses = Course.objects.annotate(student_count=Count('enrollments')).order_by('-student_count')[:5]
    recent_assignments = Assignment.objects.select_related('course').order_by('-created_at')[:5]
    recent_quiz_results = QuizResult.objects.select_related('quiz', 'student__user').order_by('-date_taken')[:5]

    teacher_report = None
    try:
        teacher_profile = request.user.teacherprofile
    except TeacherProfile.DoesNotExist:
        teacher_profile = None

    if teacher_profile is not None:
        courses = Course.objects.filter(teacher=teacher_profile)
        enrollments = Enrollment.objects.filter(course__in=courses).select_related('student__user', 'course')
        student_ids = enrollments.values_list('student_id', flat=True).distinct()
        students = StudentProfile.objects.filter(id__in=student_ids).select_related('user')

        student_rows = []
        for student in students:
            quiz_qs = QuizResult.objects.filter(student=student, quiz__course__in=courses)
            avg_quiz = quiz_qs.aggregate(avg=Avg('score'))['avg']

            assign_qs = AssignmentSubmission.objects.filter(
                student=student,
                assignment__course__in=courses,
                score__isnull=False,
            )
            avg_assignment = assign_qs.aggregate(avg=Avg('score'))['avg']

            attendance_qs = AttendanceRecord.objects.filter(student=student, course__in=courses)
            total_attendance = attendance_qs.count()
            present_count = attendance_qs.filter(status='present').count()
            attendance_pct = round((present_count / total_attendance * 100), 1) if total_attendance else None

            materials_qs = VideoWatchProgress.objects.filter(student=student, material__course__in=courses)
            total_materials = materials_qs.count()
            completed_materials = materials_qs.filter(watched_complete=True).count()
            completion_pct = round((completed_materials / total_materials * 100), 1) if total_materials else None

            flags = []
            if avg_quiz is not None and avg_quiz < 50:
                flags.append('Low quiz average')
            if avg_assignment is not None and avg_assignment < 50:
                flags.append('Low assignment average')
            if attendance_pct is not None and attendance_pct < 70:
                flags.append('Low attendance')
            if completion_pct is not None and completion_pct < 60:
                flags.append('Low material completion')
            if not flags and avg_quiz is None and avg_assignment is None and attendance_pct is None and completion_pct is None:
                flags.append('Insufficient data')

            latest_submission = AssignmentSubmission.objects.filter(
                student=student,
                assignment__course__in=courses,
            ).select_related('assignment').order_by('-submission_date').first()

            student_rows.append({
                'student': student,
                'avg_quiz': round(avg_quiz, 2) if avg_quiz is not None else None,
                'avg_assignment': round(avg_assignment, 2) if avg_assignment is not None else None,
                'attendance_pct': attendance_pct,
                'completion_pct': completion_pct,
                'flags': flags,
                'latest_submission': latest_submission,
            })

        student_rows.sort(key=lambda row: (0 if row['flags'] and row['flags'][0] != 'Insufficient data' else 1, row['student'].user.get_full_name()))

        teacher_report = {
            'courses': list(courses),
            'students': student_rows,
            'summary': {
                'total_students': len(student_rows),
                'needs_attention': sum(1 for row in student_rows if row['flags']),
            },
        }

    return render(request, 'reports/report_list.html', {
        'top_courses': top_courses,
        'recent_assignments': recent_assignments,
        'recent_quiz_results': recent_quiz_results,
        'teacher_report': teacher_report,
    })
