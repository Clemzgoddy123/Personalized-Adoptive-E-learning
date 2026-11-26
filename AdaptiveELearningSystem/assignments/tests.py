from django.test import TestCase
from django.urls import reverse


class AssignmentAccessTests(TestCase):
    def test_anonymous_user_cannot_access_assignment_pages(self):
        response = self.client.get(reverse('assignment_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        response = self.client.get(reverse('assignment_detail', args=[1]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
