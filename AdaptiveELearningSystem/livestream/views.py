from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LiveClassForm
from .models import LiveClass
from .utils import build_jitsi_embed_url, generate_jitsi_room_link

from attendance.models import AttendanceRecord
from courses.models import Course
from students.models import StudentProfile
from teachers.models import TeacherProfile
from notifications.models import Notification

@login_required
def live_class_list(request):
    live_classes = LiveClass.objects.select_related('course', 'teacher').order_by('scheduled_time')
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    student_profile = StudentProfile.objects.filter(user=request.user).first()
    can_schedule = teacher_profile is not None
    form = None

    if request.method == 'POST' and can_schedule:
        form = LiveClassForm(request.POST, user=request.user)
        if form.is_valid():
            live = form.save(teacher=teacher_profile)
            # notify enrolled students and the teacher about the new live class
            try:
                students = [enrollment.student.user for enrollment in live.course.enrollments.select_related('student__user')]
                # create a message
                msg = f"Live class scheduled for {live.course.title} at {live.scheduled_time.strftime('%Y-%m-%d %H:%M')} — join: {live.meeting_link}"
                # notify teacher
                Notification.objects.create(user=live.teacher.user, message=msg, notification_type='info')
                # notify students
                for u in students:
                    Notification.objects.create(user=u, message=msg, notification_type='info')
            except Exception:
                pass
            return redirect('live_class_list')
    elif request.method == 'POST':
        return redirect('login')

    if form is None:
        form = LiveClassForm(user=request.user)

    return render(request, 'livestream/live_class_list.html', {
        'live_classes': live_classes,
        'form': form,
        'can_schedule': can_schedule,
        'student_profile': student_profile,
        'teacher_profile': teacher_profile,
    })


@login_required
def live_class_detail(request, live_class_id):
    live_class = get_object_or_404(LiveClass, pk=live_class_id)
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()
    today = timezone.localdate()
    student_count = AttendanceRecord.objects.filter(
        course=live_class.course,
        date=today,
        status='present'
    ).count()
    can_start = (
        teacher_profile is not None
        and live_class.teacher_id == teacher_profile.id
        and live_class.status == 'scheduled'
    )
    can_end = (
        teacher_profile is not None
        and live_class.teacher_id == teacher_profile.id
        and live_class.status in ('ongoing', 'scheduled')
    )
    embed_meeting_link = build_jitsi_embed_url(live_class.meeting_link, request)

    return render(request, 'livestream/live_class_detail.html', {
        'live_class': live_class,
        'student_count': student_count,
        'can_start': can_start,
        'can_end': can_end,
        'embed_meeting_link': embed_meeting_link,
    })


@login_required
def start_live_class(request, live_class_id):
    live_class = get_object_or_404(LiveClass, pk=live_class_id)
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()

    if teacher_profile and live_class.teacher_id == teacher_profile.id and live_class.status == 'scheduled':
        live_class.status = 'ongoing'
        live_class.save(update_fields=['status'])
        messages.success(request, 'Live class started successfully.')
        # notify students
        try:
            msg = f"Live class for {live_class.course.title} is starting now — join: {live_class.meeting_link}"
            for enrollment in live_class.course.enrollments.select_related('student__user'):
                Notification.objects.create(user=enrollment.student.user, message=msg, notification_type='info')
        except Exception:
            pass
    else:
        messages.warning(request, 'Unable to start this class.')

    return redirect('live_class_detail', live_class_id=live_class_id)


@login_required
def generate_new_jitsi_link(request, live_class_id):
    live_class = get_object_or_404(LiveClass, pk=live_class_id)
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()

    if request.method == 'POST' and teacher_profile and live_class.teacher_id == teacher_profile.id:
        live_class.meeting_link = generate_jitsi_room_link(live_class.course, live_class.scheduled_time)
        live_class.save(update_fields=['meeting_link'])
        messages.success(request, f'Live class link generated: {live_class.meeting_link}')
        # notify students about updated link
        try:
            msg = f"Live class link updated for {live_class.course.title}. New link: {live_class.meeting_link}"
            for enrollment in live_class.course.enrollments.select_related('student__user'):
                Notification.objects.create(user=enrollment.student.user, message=msg, notification_type='info')
        except Exception:
            pass
    elif request.method != 'POST':
        messages.warning(request, 'Use the Generate New Link button to create a live class link.')
    else:
        messages.warning(request, 'You can only generate links for your own live classes.')

    return redirect('live_class_list')


@login_required
def cancel_live_class(request, live_class_id):
    live_class = get_object_or_404(LiveClass, pk=live_class_id)
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()

    if teacher_profile and live_class.teacher_id == teacher_profile.id and live_class.status in ('scheduled', 'ongoing'):
        live_class.status = 'cancelled'
        live_class.save(update_fields=['status'])
        messages.success(request, 'Live class canceled successfully.')
        # notify students
        try:
            msg = f"Live class for {live_class.course.title} scheduled at {live_class.scheduled_time.strftime('%Y-%m-%d %H:%M')} has been cancelled."
            for enrollment in live_class.course.enrollments.select_related('student__user'):
                Notification.objects.create(user=enrollment.student.user, message=msg, notification_type='warning')
        except Exception:
            pass
    else:
        messages.warning(request, 'Unable to cancel this class.')

    return redirect('live_class_detail', live_class_id=live_class_id)


@login_required
def end_live_class(request, live_class_id):
    live_class = get_object_or_404(LiveClass, pk=live_class_id)
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()

    if teacher_profile and live_class.teacher_id == teacher_profile.id and live_class.status in ('ongoing', 'scheduled'):
        # mark class completed
        live_class.status = 'completed'
        live_class.save(update_fields=['status'])

        # mark absent for enrolled students who do not already have attendance records
        try:
            # any students who already have a present record will be skipped by manager
            AttendanceRecord.objects.mark_absent_for_liveclass(live_class)
            messages.success(request, 'Live class ended and attendance recorded (absentees marked).')
        except Exception:
            messages.warning(request, 'Live class ended but attendance could not be recorded automatically.')
        # notify students that class has ended
        try:
            msg = f"Live class for {live_class.course.title} has ended. Attendance has been recorded where available."
            for enrollment in live_class.course.enrollments.select_related('student__user'):
                Notification.objects.create(user=enrollment.student.user, message=msg, notification_type='info')
        except Exception:
            pass
    else:
        messages.warning(request, 'Unable to end this class.')

    return redirect('live_class_detail', live_class_id=live_class_id)


@login_required
def delete_live_class(request, live_class_id):
    live_class = get_object_or_404(LiveClass, pk=live_class_id)
    teacher_profile = TeacherProfile.objects.filter(user=request.user).first()

    # allow deletion only by the owning teacher and only after completed or cancelled
    if teacher_profile and live_class.teacher_id == teacher_profile.id and live_class.status in ('completed', 'cancelled'):
        course_title = live_class.course.title
        scheduled = live_class.scheduled_time
        try:
            # collect recipients before deletion
            recipients = [enrollment.student.user for enrollment in live_class.course.enrollments.select_related('student__user')]
            live_class.delete()
            messages.success(request, 'Live class link deleted successfully.')
            # notify students that the link was removed
            msg = f"Live class for {course_title} scheduled at {scheduled.strftime('%Y-%m-%d %H:%M')} has been removed by the teacher."
            for u in recipients:
                Notification.objects.create(user=u, message=msg, notification_type='info')
        except Exception:
            messages.warning(request, 'Unable to delete the live class.')
    else:
        messages.warning(request, 'You are not allowed to delete this live class.')

    return redirect('live_class_list')
