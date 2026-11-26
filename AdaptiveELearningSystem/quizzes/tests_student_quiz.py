from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from courses.models import Course
from students.models import StudentProfile
from teachers.models import TeacherProfile

from .models import Question, Quiz, QuizQuestion, QuizResult


class StudentQuizTests(TestCase):
    def setUp(self):
        self.teacher_user = get_user_model().objects.create_user(
            username='quiz-teacher',
            password='test-password',
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        self.student_user = get_user_model().objects.create_user(
            username='student-user',
            password='student-password',
        )
        self.student = StudentProfile.objects.create(user=self.student_user)
        self.course = Course.objects.create(
            title='Biology',
            subject='Science',
            class_level='10',
            teacher=self.teacher,
        )
        self.course.enrollments.create(student=self.student)
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Biology Review',
            total_marks=4,
            duration_minutes=15,
        )
        self.question1 = Question.objects.create(
            course=self.course,
            text='Question 1',
            option_a='Answer A',
            option_b='Answer B',
            option_c='Answer C',
            option_d='Answer D',
            correct_choice='A',
            marks=1,
        )
        self.question2 = Question.objects.create(
            course=self.course,
            text='Question 2',
            option_a='Answer A',
            option_b='Answer B',
            option_c='Answer C',
            option_d='Answer D',
            correct_choice='B',
            marks=1,
        )
        QuizQuestion.objects.create(quiz=self.quiz, question=self.question1, order=0)
        QuizQuestion.objects.create(quiz=self.quiz, question=self.question2, order=1)
        self.client.login(username='student-user', password='student-password')

    def test_student_can_view_quiz_list_and_take_quiz(self):
        response = self.client.get(reverse('quiz_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Biology Review')
        self.assertContains(response, 'Take Quiz')

    def test_student_can_submit_quiz_answers(self):
        response = self.client.post(reverse('student_take_quiz', args=[self.quiz.id]), {
            f'question_{self.question1.id}': 'A',
            f'question_{self.question2.id}': 'B',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quiz submitted')
        self.assertContains(response, 'You scored')
        self.assertContains(response, '4')
        result = QuizResult.objects.get(quiz=self.quiz, student=self.student)
        self.assertEqual(result.score, 2)

    def test_student_cannot_take_quiz_if_not_enrolled(self):
        other_user = get_user_model().objects.create_user(
            username='other-user',
            password='other-password',
        )
        StudentProfile.objects.create(user=other_user)
        self.client.logout()
        self.client.login(username='other-user', password='other-password')

        response = self.client.get(reverse('student_take_quiz', args=[self.quiz.id]))
        self.assertEqual(response.status_code, 404)
