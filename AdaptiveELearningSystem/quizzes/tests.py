from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Enrollment
from students.models import StudentProfile
from teachers.models import TeacherProfile

from .models import Question, Quiz, QuizQuestion


class QuizCreationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='quiz-teacher',
            password='test-password',
        )
        self.teacher = TeacherProfile.objects.create(user=self.user)
        self.course = Course.objects.create(
            title='Biology',
            subject='Science',
            class_level='10',
            teacher=self.teacher,
        )
        self.client.login(username='quiz-teacher', password='test-password')

    def create_question(self, number):
        return Question.objects.create(
            course=self.course,
            text=f'Question {number}',
            option_a='Answer A',
            option_b='Answer B',
            option_c='Answer C',
            option_d='Answer D',
            correct_choice='A',
            marks=1,
        )

    def test_teacher_can_create_quiz_with_random_course_questions(self):
        for number in range(1, 4):
            self.create_question(number)

        response = self.client.post(reverse('teacher_quiz_create'), {
            'course': self.course.pk,
            'title': 'Biology Review',
            'total_marks': 30,
            'duration_minutes': 25,
            'num_questions': 2,
        })

        self.assertRedirects(response, reverse('quiz_list'))
        quiz = Quiz.objects.get(title='Biology Review')
        self.assertEqual(quiz.quiz_questions.count(), 2)
        self.assertEqual(
            set(quiz.quiz_questions.values_list('question__course_id', flat=True)),
            {self.course.pk},
        )

    def test_quiz_is_not_created_when_question_bank_is_too_small(self):
        self.create_question(1)

        response = self.client.post(reverse('teacher_quiz_create'), {
            'course': self.course.pk,
            'title': 'Incomplete Quiz',
            'total_marks': 30,
            'duration_minutes': 25,
            'num_questions': 2,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Only 1 question(s) are available')
        self.assertFalse(Quiz.objects.filter(title='Incomplete Quiz').exists())

    def test_quiz_list_renders_question_count(self):
        question = self.create_question(1)
        quiz = Quiz.objects.create(
            course=self.course,
            title='Existing Quiz',
            total_marks=10,
            duration_minutes=10,
        )
        QuizQuestion.objects.create(quiz=quiz, question=question)

        response = self.client.get(reverse('quiz_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Existing Quiz')
        self.assertEqual(response.context['quizzes'][0].question_count, 1)

    def test_teacher_can_create_quiz_with_manual_question_form(self):
        response = self.client.post(reverse('teacher_quiz_create'), {
            'course': self.course.pk,
            'title': 'Manual Quiz',
            'total_marks': 10,
            'duration_minutes': 20,
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-text': 'What is 2 + 2?',
            'form-0-option_a': '3',
            'form-0-option_b': '4',
            'form-0-option_c': '5',
            'form-0-option_d': '6',
            'form-0-correct_choice': 'B',
            'form-0-marks': '5',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('quiz_list'))
        quiz = Quiz.objects.get(title='Manual Quiz')
        self.assertEqual(quiz.question_count, 1)

    def test_student_cannot_access_quiz_creation_page(self):
        student_user = get_user_model().objects.create_user(
            username='quiz-student-only',
            password='test-password',
        )
        StudentProfile.objects.create(user=student_user)
        self.client.login(username='quiz-student-only', password='test-password')

        response = self.client.get(reverse('teacher_quiz_create'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))


class AdminRegistryTests(TestCase):
    def test_project_models_are_registered_in_admin(self):
        registry = {model._meta.label_lower for model in admin.site._registry}

        self.assertIn('quizzes.quizquestion', registry)
        self.assertIn('courses.videowatchprogress', registry)


class QuizAccessTests(TestCase):
    def setUp(self):
        self.teacher_user = get_user_model().objects.create_user(
            username='quiz-teacher-access',
            password='test-password',
        )
        self.teacher_profile = TeacherProfile.objects.create(user=self.teacher_user)

        self.student_user = get_user_model().objects.create_user(
            username='quiz-student-access',
            password='test-password',
        )
        self.student_profile = StudentProfile.objects.create(user=self.student_user)

        self.course = Course.objects.create(
            title='Biology',
            subject='Science',
            class_level='10',
            teacher=self.teacher_profile,
        )
        Enrollment.objects.create(student=self.student_profile, course=self.course)

        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Biology Review',
            total_marks=30,
            duration_minutes=25,
        )
        self.question = Question.objects.create(
            course=self.course,
            text='What is the powerhouse of the cell?',
            option_a='Nucleus',
            option_b='Ribosome',
            option_c='Mitochondria',
            option_d='Cell membrane',
            correct_choice='C',
            marks=1,
        )
        QuizQuestion.objects.create(quiz=self.quiz, question=self.question, order=0)

    def test_student_can_view_quiz_questions(self):
        self.client.login(username='quiz-student-access', password='test-password')

        response = self.client.get(reverse('student_view_quiz_questions', args=[self.quiz.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'What is the powerhouse of the cell?')
        self.assertContains(response, 'Mitochondria')
        self.assertContains(response, 'View quiz questions')
