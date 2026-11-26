import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from students.models import StudentProfile
from teachers.models import TeacherProfile

User = get_user_model()
client = Client()

users = [
    ('test_student', 'student@example.com', 'studentpass', 'student'),
    ('test_teacher', 'teacher@example.com', 'teacherpass', 'teacher'),
]

print('setup done')
for username, email, password, role in users:
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    if created or not user.check_password(password):
        user.set_password(password)
        user.save()
    if role == 'student':
        StudentProfile.objects.get_or_create(user=user)
    else:
        TeacherProfile.objects.get_or_create(user=user)

    login_ok = client.login(username=username, password=password)
    print(f'user {username} login {login_ok}')

    for url in ['/accounts/profile/', '/students/', '/teachers/']:
        r = client.get(url)
        print(username, url, r.status_code)

    if role == 'student':
        r = client.get('/students/')
        print('student dash ok', 'Student Dashboard' in r.content.decode('utf-8'))
    if role == 'teacher':
        r = client.get('/teachers/')
        print('teacher dash ok', 'Teacher Dashboard' in r.content.decode('utf-8'))
