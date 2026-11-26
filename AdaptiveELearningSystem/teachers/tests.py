from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from courses.models import Course, LearningMaterial, Enrollment
from notifications.models import Notification
from students.models import StudentProfile

from .models import TeacherProfile


class TeacherTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='material-teacher',
            password='test-password',
        )
        self.teacher = TeacherProfile.objects.create(user=self.user)
        self.course = Course.objects.create(
            title='Science',
            subject='Science',
            class_level='10',
            teacher=self.teacher,
        )
        other_user = get_user_model().objects.create_user(
            username='other-teacher',
            password='test-password',
        )
        other_teacher = TeacherProfile.objects.create(user=other_user)
        self.other_course = Course.objects.create(
            title='History',
            subject='History',
            class_level='10',
            teacher=other_teacher,
        )
        self.client.login(username='material-teacher', password='test-password')

    def tearDown(self):
        LearningMaterial.objects.all().delete()

    def test_teacher_can_upload_pdf_to_owned_course(self):
        upload = SimpleUploadedFile('lesson.pdf', b'%PDF-1.4 test', content_type='application/pdf')

        response = self.client.post(reverse('upload_learning_material'), {
            'course': self.course.pk,
            'title': 'Lesson PDF',
            'material_type': 'pdf',
            'file_path': upload,
        })

        self.assertRedirects(response, reverse('teacher_dashboard'))
        material = LearningMaterial.objects.get(title='Lesson PDF')
        self.assertEqual(material.course, self.course)
        self.assertEqual(material.material_type, 'pdf')

    def test_teacher_cannot_upload_to_another_teachers_course(self):
        upload = SimpleUploadedFile('lesson.pdf', b'%PDF-1.4 test', content_type='application/pdf')

        response = self.client.post(reverse('upload_learning_material'), {
            'course': self.other_course.pk,
            'title': 'Wrong Course',
            'material_type': 'pdf',
            'file_path': upload,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a valid choice')
        self.assertFalse(LearningMaterial.objects.filter(title='Wrong Course').exists())

    def test_teacher_cannot_upload_unsupported_file_type(self):
        upload = SimpleUploadedFile('lesson.txt', b'plain text', content_type='text/plain')

        response = self.client.post(reverse('upload_learning_material'), {
            'course': self.course.pk,
            'title': 'Text File',
            'material_type': 'pdf',
            'file_path': upload,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Only PDF, DOC, DOCX, MP4, MOV, AVI, and WEBM files are allowed.')
        self.assertFalse(LearningMaterial.objects.filter(title='Text File').exists())

    def test_video_material_reports_correct_mime_type(self):
        upload = SimpleUploadedFile('tutorial.mov', b'video-bytes', content_type='video/quicktime')
        material = LearningMaterial.objects.create(
            course=self.course,
            title='Intro Video',
            material_type='video',
            file_path=upload,
        )

        self.assertEqual(material.get_media_mime_type(), 'video/quicktime')

    def test_teacher_can_upload_video_and_message_students(self):
        student_user = get_user_model().objects.create_user(
            username='student-one',
            password='test-password',
        )
        student_profile = StudentProfile.objects.create(user=student_user)
        Enrollment.objects.create(student=student_profile, course=self.course)

        upload = SimpleUploadedFile('tutorial.mp4', b'video-bytes', content_type='video/mp4')

        response = self.client.post(reverse('upload_learning_material'), {
            'course': self.course.pk,
            'title': 'Video Tutorial',
            'material_type': 'video',
            'file_path': upload,
            'message_text': 'Please watch this tutorial before class.',
        })

        self.assertRedirects(response, reverse('teacher_dashboard'))
        material = LearningMaterial.objects.get(title='Video Tutorial')
        self.assertEqual(material.material_type, 'video')
        self.assertEqual(material.message_text, 'Please watch this tutorial before class.')
        self.assertTrue(Notification.objects.filter(user=student_user, message__icontains='tutorial').exists())

    def test_teacher_can_view_enrolled_students(self):
        student_user = get_user_model().objects.create_user(
            username='dashboard-student',
            first_name='Test',
            last_name='Student',
            password='test-password',
        )
        student_profile = StudentProfile.objects.create(user=student_user, class_level='10')
        Enrollment.objects.create(student=student_profile, course=self.course)

        response = self.client.get(reverse('view_student'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Student')
        self.assertContains(response, 'Science')

    def test_teacher_cannot_filter_by_another_teachers_course(self):
        response = self.client.get(reverse('view_students_by_course', args=[self.other_course.id]))

        self.assertRedirects(response, reverse('view_student'))
