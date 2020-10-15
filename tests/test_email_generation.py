from django.contrib.auth import get_user_model
from django.test import TestCase, Client, tag
from django.urls import reverse
from django.urls import reverse
from datetime import datetime, timedelta

from djangoplicity.newsletters.models import NewsletterType, Newsletter, MailerParameter, Mailer


class TestEmailGeneration(TestCase):
    fixtures = ['newsletters']

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@newsletters.org',
            password='password123'
        )
        self.client.force_login(self.admin_user)

    @classmethod
    def setUpTestData(cls):
        cls.mailer = Newsletter.objects.get(pk=10000)
        cls.newsletter_type = NewsletterType.objects.get(pk=10000)
        cls.newsletter = Newsletter.objects.get(pk=10000)

    def test_newsletter_admin_html(self):
        """Test newsletter html on admin is properly rendered"""
        url = '/admin/newsletters/newsletter/%s/html/' % self.newsletter.pk
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.newsletter.editorial)

    def test_newsletter_admin_text(self):
        """Test newsletter text on admin is properly rendered"""
        url = '/admin/newsletters/newsletter/%s/text/' % self.newsletter.pk
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.newsletter.editorial_text)

    def test_newsletter_detail_html(self):
        """Test newsletter html is properly rendered"""
        url = '/newsletters/%s/html/%s/' % (self.newsletter_type.slug, self.newsletter.pk)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, """<iframe src="/newsletters/{0}/htmlembed/{1}/" width="100%" scrolling="no" frameBorder="0" onload='javascript:resizeIframe(this);'></iframe>""".format(self.newsletter_type.slug, self.newsletter.pk))

    def test_newsletter_embed_html(self):
        """Test newsletter embed html is properly rendered"""
        url = '/newsletters/%s/htmlembed/%s/' % (self.newsletter_type.slug, self.newsletter.pk)
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.newsletter.editorial)
