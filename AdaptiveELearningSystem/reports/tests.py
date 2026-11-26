from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assignments.models import Assignment, AssignmentSubmission
from attendance.models import AttendanceRecord
from courses.models import Course, Enrollment, LearningMaterial, VideoWatchProgress
from quizzes.models import Quiz, QuizResult
from students.models import StudentProfile
from teachers.models import TeacherProfile


class ReportsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reportsuser', password='StrongPass123!')

    def test_reports_page_requires_login(self):
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_reports_page_renders_for_authenticated_user(self):
        self.client.login(username='reportsuser', password='StrongPass123!')
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reports')

    def test_teacher_reports_include_decision_support(self):
        teacher_user = User.objects.create_user(username='teacher_reports', password='StrongPass123!')
        teacher_profile = TeacherProfile.objects.create(user=teacher_user, subject_specialization='Mathematics')
        student_user = User.objects.create_user(username='student_reports', password='StrongPass123!')
        student_profile = StudentProfile.objects.create(user=student_user, class_level='Grade 8')

        course = Course.objects.create(
            title='Algebra Foundations',
            description='Early algebra concepts',
            subject='Mathematics',
            class_level='Grade 8',
            teacher=teacher_profile,
        )
        Enrollment.objects.create(student=student_profile, course=course)

        quiz = Quiz.objects.create(course=course, title='Unit 1 Quiz', total_marks=100)
        QuizResult.objects.create(quiz=quiz, student=student_profile, score=40)

        assignment = Assignment.objects.create(
            course=course,
            title='Homework 1',
            description='Practice set',
            deadline=timezone.now() + timedelta(days=7),
            max_score=100,
        )
        AssignmentSubmission.objects.create(assignment=assignment, student=student_profile, score=45)

        AttendanceRecord.objects.create(course=course, student=student_profile, date=date.today(), status='absent')

        material = LearningMaterial.objects.create(
            course=course,
            title='Intro video',
            material_type='note',
            note_text='Watch this guide before class.',
        )
        VideoWatchProgress.objects.create(material=material, student=student_profile, watched_complete=False)

        self.client.login(username='teacher_reports', password='StrongPass123!')
        response = self.client.get(reverse('report_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Decision support')
        self.assertContains(response, 'Algebra Foundations')
        self.assertContains(response, 'Needs attention')
