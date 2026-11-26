from django.test import RequestFactory, TestCase

from .views import build_jitsi_embed_url


class JitsiEmbedUrlTests(TestCase):
    def test_build_jitsi_embed_url_adds_embed_parameters(self):
        factory = RequestFactory()
        request = factory.get('/livestream/1/')

        embed_url = build_jitsi_embed_url('https://meet.jit.si/adaptive-room', request)

        self.assertIn('embed=true', embed_url)
        self.assertIn('mobile=true', embed_url)
        self.assertIn('parent=testserver', embed_url)
