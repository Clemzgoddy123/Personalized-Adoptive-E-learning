from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AnalyticsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='analyticsuser', password='StrongPass123!')

    def test_analytics_dashboard_requires_login(self):
        response = self.client.get(reverse('analytics_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_analytics_dashboard_renders_for_authenticated_user(self):
        self.client.login(username='analyticsuser', password='StrongPass123!')
        response = self.client.get(reverse('analytics_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')
