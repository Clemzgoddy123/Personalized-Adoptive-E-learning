import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from teachers.models import TeacherProfile
from students.models import StudentProfile
from courses.models import Course, Enrollment
from livestream.models import LiveClass
from livestream.utils import generate_jitsi_room_link
from notifications.models import Notification

PASSWORD = 'DemoPass123!'

# create teacher user
teacher, created = User.objects.get_or_create(username='demo_teacher', defaults={'first_name':'Demo','last_name':'Teacher','email':'demo_teacher@example.com'})
if created:
    teacher.set_password(PASSWORD)
    teacher.save()
    print('Created teacher user')
else:
    print('Teacher user exists')

teacher_profile, _ = TeacherProfile.objects.get_or_create(user=teacher, defaults={'subject_specialization':'Mathematics','qualification':'MSc Education'})

# create student user
student, created = User.objects.get_or_create(username='demo_student', defaults={'first_name':'Demo','last_name':'Student','email':'demo_student@example.com'})
if created:
    student.set_password(PASSWORD)
    student.save()
    print('Created student user')
else:
    print('Student user exists')

student_profile, _ = StudentProfile.objects.get_or_create(user=student, defaults={'class_level':'Grade 9'})

# create a course for the teacher
course, created = Course.objects.get_or_create(title='Demo Algebra', defaults={'description':'Demo course','subject':'Algebra','class_level':'Grade 9','teacher':teacher_profile})
if not created and course.teacher_id != teacher_profile.id:
    course.teacher = teacher_profile
    course.save()

# enroll student
Enrollment.objects.get_or_create(student=student_profile, course=course)

# create a live class scheduled 3 minutes from now
scheduled = timezone.now() + timedelta(minutes=3)
meeting_link = generate_jitsi_room_link(course, scheduled)
live = LiveClass.objects.create(course=course, teacher=teacher_profile, scheduled_time=scheduled, meeting_link=meeting_link, status='scheduled')
print('Created LiveClass id=', live.id)

# create notifications for teacher and student
msg = f"Live class scheduled for {course.title} at {scheduled.strftime('%Y-%m-%d %H:%M')} — join: {meeting_link}"
Notification.objects.create(user=teacher, message=msg, notification_type='info')
Notification.objects.create(user=student, message=msg, notification_type='info')

print('Demo setup complete. Credentials:')
print('teacher:', 'demo_teacher', PASSWORD)
print('student:', 'demo_student', PASSWORD)
print('Live class id:', live.id)
print('Open: /livestream/{}/'.format(live.id))
