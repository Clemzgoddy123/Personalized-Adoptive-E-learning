from django.test import TestCase
from django.urls import reverse


class AttendanceAccessTests(TestCase):
    def test_anonymous_user_cannot_access_attendance_page(self):
        response = self.client.get(reverse('attendance_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
