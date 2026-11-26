from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from students.models import StudentProfile
from teachers.models import TeacherProfile


class AuthFlowTests(TestCase):
    def test_home_dashboard_links_point_to_login(self):
        response = self.client.get('/')
        self.assertContains(response, '/accounts/login/?next=/students/')
        self.assertContains(response, '/accounts/login/?next=/teachers/')

    def test_registration_saves_user_and_profile(self):
        response = self.client.post('/accounts/register/?next=/students/', {
            'username': 'newstudent',
            'email': 'student@example.com',
            'role': 'student',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/students/')
        self.assertTrue(User.objects.filter(username='newstudent').exists())
        self.assertTrue(StudentProfile.objects.filter(user__username='newstudent').exists())

    def test_registration_appends_to_sql_backup(self):
        sql_path = Path(__file__).resolve().parents[2] / 'e-learning_db.session.sql'
        original = sql_path.read_text(encoding='utf-8') if sql_path.exists() else ''

        try:
            response = self.client.post('/accounts/register/?next=/teachers/', {
                'username': 'newteacher',
                'email': 'teacher@example.com',
                'role': 'teacher',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            })

            self.assertEqual(response.status_code, 302)
            updated = sql_path.read_text(encoding='utf-8')
            self.assertIn('newteacher', updated)
            self.assertIn('teacher@example.com', updated)
            self.assertIn('teacher', updated)
        finally:
            if sql_path.exists():
                sql_path.write_text(original, encoding='utf-8')

    def test_teacher_with_student_profile_cannot_access_student_dashboard(self):
        user = User.objects.create_user(username='mixed-role-teacher', password='StrongPass123!')
        TeacherProfile.objects.create(user=user)
        StudentProfile.objects.create(user=user)

        self.client.login(username='mixed-role-teacher', password='StrongPass123!')
        response = self.client.get(reverse('student_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_student_with_teacher_profile_cannot_access_teacher_dashboard(self):
        user = User.objects.create_user(username='mixed-role-student', password='StrongPass123!')
        StudentProfile.objects.create(user=user)
        TeacherProfile.objects.create(user=user)

        self.client.login(username='mixed-role-student', password='StrongPass123!')
        response = self.client.get(reverse('teacher_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
