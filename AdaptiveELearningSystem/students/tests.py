from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assignments.models import Assignment, AssignmentSubmission
from courses.models import Course, Enrollment
from notifications.models import Notification
from quizzes.models import Quiz, QuizResult
from .models import StudentProfile
from teachers.models import TeacherProfile


class StudentDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='student-dashboard-user',
            password='test-password',
            first_name='Dashboard',
            last_name='Student',
        )
        self.student = StudentProfile.objects.create(user=self.user, class_level='10')
        self.teacher_user = get_user_model().objects.create_user(
            username='dashboard-teacher',
            password='test-password',
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        self.course = Course.objects.create(
            title='Mathematics',
            subject='Math',
            class_level='10',
            teacher=self.teacher,
        )
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_dashboard_renders_student_data_and_recommendations(self):
        assignment = Assignment.objects.create(
            course=self.course,
            title='Algebra Practice',
            deadline=timezone.now() + timedelta(days=2),
        )
        AssignmentSubmission.objects.create(
            assignment=assignment,
            student=self.student,
            submission_file='algebra.pdf',
        )
        Notification.objects.create(
            user=self.user,
            message='New course material',
            notification_type='info',
            read_status=False,
        )

        self.client.login(username='student-dashboard-user', password='test-password')
        response = self.client.get(reverse('student_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'students/student_dashboard.html')
        self.assertContains(response, 'Mathematics')
        self.assertContains(response, 'Algebra Practice')
        self.assertContains(response, 'Review work for Algebra Practice')
        self.assertEqual(response.context['assignment_progress']['completed'], 1)
        self.assertEqual(response.context['assignment_progress']['percent'], 100)
        self.assertEqual(response.context['unread_notifications'], 1)

    def test_dashboard_handles_authenticated_user_without_student_profile(self):
        StudentProfile.objects.filter(pk=self.student.pk).delete()
        self.client.login(username='student-dashboard-user', password='test-password')

        response = self.client.get(reverse('student_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student profile not found')
        self.assertEqual(response.context['recommendations'], [])

    def test_dashboard_with_student_profile_and_no_enrollments_still_generates_recommendations(self):
        self.student.enrollments.all().delete()
        self.client.login(username='student-dashboard-user', password='test-password')

        response = self.client.get(reverse('student_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student Dashboard')
        self.assertTrue(response.context['recommendations'])
        self.assertEqual(response.context['recommendations'][0].course_title, 'General')

    def test_dashboard_injects_chart_json_for_client_side_charts(self):
        self.client.login(username='student-dashboard-user', password='test-password')
        response = self.client.get(reverse('student_dashboard'))

        self.assertContains(response, 'id="assignment-labels"')
        self.assertContains(response, 'id="assignment-scores"')
        self.assertContains(response, 'id="performance-labels"')
        self.assertContains(response, 'id="attendance-labels"')

    def test_dashboard_handles_zero_division_edge_cases(self):
        assignment = Assignment.objects.create(
            course=self.course,
            title='Zero Max Score Assignment',
            deadline=timezone.now() + timedelta(days=1),
            max_score=0,
        )
        AssignmentSubmission.objects.create(
            assignment=assignment,
            student=self.student,
            score=10,
            feedback='Needs improvement',
        )
        quiz = Quiz.objects.create(course=self.course, title='Zero Mark Quiz', total_marks=0)
        QuizResult.objects.create(quiz=quiz, student=self.student, score=5)

        self.client.login(username='student-dashboard-user', password='test-password')
        response = self.client.get(reverse('student_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student Dashboard')
        self.assertEqual(response.context['performance_metrics']['average_assignment_percent'], 0)
        self.assertEqual(response.context['performance_metrics']['average_quiz_percent'], 0)
