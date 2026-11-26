from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q

from students.models import StudentProfile
from teachers.models import TeacherProfile
from quizzes.models import QuizResult
from assignments.models import AssignmentSubmission
from attendance.models import AttendanceRecord
from courses.models import Enrollment, VideoWatchProgress


@login_required
def decision_support(request):
    """Teacher Decision Support dashboard.

    Aggregates per-student indicators (quiz avg, assignment avg, attendance %,
    material completion %) for courses taught by the logged-in teacher and
    highlights students who may require additional support.
    """
    # try to find teacher profile
    try:
        teacher = request.user.teacherprofile
    except TeacherProfile.DoesNotExist:
        return render(request, 'teacher_support/decision_support.html', {
            'error': 'Teacher profile not found for current user.'
        })

    courses = teacher.courses.all()

    # collect students enrolled in any of the teacher's courses
    enrollments = Enrollment.objects.filter(course__in=courses).select_related('student', 'course')
    student_ids = enrollments.values_list('student_id', flat=True).distinct()

    students = StudentProfile.objects.filter(id__in=student_ids)

    results = []

    for student in students:
        # average quiz score across teacher's courses
        quiz_qs = QuizResult.objects.filter(student=student, quiz__course__in=courses)
        avg_quiz = quiz_qs.aggregate(avg=Avg('score'))['avg']

        # average assignment score
        assign_qs = AssignmentSubmission.objects.filter(student=student, assignment__course__in=courses, score__isnull=False)
        avg_assignment = assign_qs.aggregate(avg=Avg('score'))['avg']

        # attendance percentage for records that exist for these courses
        attendance_qs = AttendanceRecord.objects.filter(student=student, course__in=courses)
        total_attendance = attendance_qs.count()
        present_count = attendance_qs.filter(status='present').count()
        attendance_pct = (present_count / total_attendance * 100) if total_attendance else None

        # material completion percentage (video watch progress)
        materials_qs = VideoWatchProgress.objects.filter(student=student, material__course__in=courses)
        total_materials = materials_qs.count()
        completed_materials = materials_qs.filter(watched_complete=True).count()
        completion_pct = (completed_materials / total_materials * 100) if total_materials else None

        # heuristic flags
        flags = []
        if avg_quiz is not None and avg_quiz < 50:
            flags.append('Low quiz average')
        if avg_assignment is not None and avg_assignment < 50:
            flags.append('Low assignment average')
        if attendance_pct is not None and attendance_pct < 70:
            flags.append('Low attendance')
        if completion_pct is not None and completion_pct < 60:
            flags.append('Low material completion')
        if avg_quiz is None and avg_assignment is None and attendance_pct is None and completion_pct is None:
            flags.append('Insufficient data')

        # find latest submission for this student in teacher's courses (if any)
        latest_submission = AssignmentSubmission.objects.filter(
            student=student, assignment__course__in=courses
        ).order_by('-submission_date').select_related('assignment').first()

        results.append({
            'student': student,
            'avg_quiz': round(avg_quiz, 2) if avg_quiz is not None else None,
            'avg_assignment': round(avg_assignment, 2) if avg_assignment is not None else None,
            'attendance_pct': round(attendance_pct, 1) if attendance_pct is not None else None,
            'completion_pct': round(completion_pct, 1) if completion_pct is not None else None,
            'flags': flags,
            'latest_submission': latest_submission,
        })

    # sort flagged students first
    results.sort(key=lambda r: (0 if r['flags'] and r['flags'][0] != 'Insufficient data' else 1, r['student'].user.get_full_name()))

    return render(request, 'teacher_support/decision_support.html', {
        'courses': courses,
        'results': results,
    })
