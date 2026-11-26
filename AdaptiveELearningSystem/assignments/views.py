from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from .models import Assignment, AssignmentSubmission
from students.models import StudentProfile
from teachers.models import TeacherProfile
from attendance.models import AttendanceRecord
from django.utils.dateparse import parse_datetime
from django.contrib import messages


@login_required
def assignment_list(request):
    assignments = Assignment.objects.select_related('course').all()
    teacher_profile = None
    if request.user.is_authenticated:
        teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    return render(request, 'assignments/assignment_list.html', {'assignments': assignments, 'teacher_profile': teacher_profile})


@login_required
def create_assignment(request):
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    if not teacher_profile:
        return redirect('assignment_list')

    # Only allow selecting courses taught by this teacher
    courses = teacher_profile.courses.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        course_id = request.POST.get('course')
        deadline_raw = request.POST.get('deadline', '').strip()
        max_score_raw = request.POST.get('max_score', '').strip()

        if not title or not course_id or not deadline_raw:
            messages.error(request, 'Title, course and deadline are required.')
        else:
            course = courses.filter(pk=course_id).first()
            if not course:
                messages.error(request, 'Invalid course selection.')
            else:
                deadline = parse_datetime(deadline_raw)
                try:
                    max_score = int(max_score_raw) if max_score_raw else 100
                except ValueError:
                    messages.error(request, 'Max score must be a number.')
                    max_score = None

                if not deadline:
                    messages.error(request, 'Please provide a valid deadline (use the date/time picker).')
                else:
                    Assignment.objects.create(
                        course=course,
                        title=title,
                        description=description,
                        deadline=deadline,
                        max_score=max_score or 100,
                    )
                    messages.success(request, 'Assignment created successfully.')
                    return redirect('assignment_list')
    return render(request, 'assignments/create_assignment.html', {
        'courses': courses,
    })


@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    submissions = assignment.submissions.select_related('student')
    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment,
        'submissions': submissions,
    })


@login_required
def download_submission_score(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission, pk=submission_id)
    if request.user != submission.student.user:
        teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
        if not teacher_profile or submission.assignment.course.teacher_id != teacher_profile.id:
            return redirect('assignment_detail', assignment_id=submission.assignment_id)

    filename = f"{submission.assignment.title}_score_{submission.student.user.username}.txt"
    content_lines = [
        f"Student: {submission.student.user.get_full_name() or submission.student.user.username}",
        f"Assignment: {submission.assignment.title}",
        f"Course: {submission.assignment.course.title}",
        f"Score: {submission.score if submission.score is not None else 'Not graded yet'}",
        f"Feedback: {submission.feedback or 'No feedback'}",
        f"Submitted: {submission.submission_date.strftime('%Y-%m-%d %H:%M')}",
    ]
    response = HttpResponse("\n".join(content_lines), content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    student_profile = StudentProfile.objects.filter(user=request.user).first()
    message = ''

    if request.method == 'POST' and student_profile:
        uploaded_file = request.FILES.get('submission_file')
        if uploaded_file:
            AssignmentSubmission.objects.update_or_create(
                assignment=assignment,
                student=student_profile,
                defaults={'submission_file': uploaded_file},
            )
            # Mark student present for this course on submission date
            try:
                AttendanceRecord.objects.mark_present(assignment.course, student_profile)
            except Exception:
                # avoid breaking submission flow if attendance creation fails
                pass
            return redirect('assignment_detail', assignment_id=assignment.pk)
        message = 'Please upload a file for the submission.'

    return render(request, 'assignments/submit_assignment.html', {
        'assignment': assignment,
        'message': message,
    })


@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission, pk=submission_id)
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    if not teacher_profile or submission.assignment.course.teacher_id != teacher_profile.id:
        return redirect('assignment_detail', assignment_id=submission.assignment_id)

    message = ''
    if request.method == 'POST':
        score = request.POST.get('score', '').strip()
        feedback = request.POST.get('feedback', '').strip()
        if score:
            try:
                submission.score = float(score)
                submission.feedback = feedback
                submission.save(update_fields=['score', 'feedback'])
                return redirect('assignment_detail', assignment_id=submission.assignment_id)
            except ValueError:
                message = 'Please enter a valid numeric score.'
        else:
            message = 'Score is required to grade this submission.'

    return render(request, 'assignments/grade_submission.html', {
        'submission': submission,
        'message': message,
    })
