from django.contrib.auth import get_user_model
from django.test import TestCase, Client, tag
from django.urls import reverse
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

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
        """Test newsletter html view on admin is properly rendered"""
        url = '/admin/newsletters/newsletter/%s/html/' % self.newsletter.pk
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.newsletter.editorial)

    def test_newsletter_admin_text(self):
        """Test newsletter text view on admin is properly rendered"""
        url = '/admin/newsletters/newsletter/%s/text/' % self.newsletter.pk
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.newsletter.editorial_text)

    def test_newsletter_admin_html_raises_404(self):
        """Test newsletter html view on admin raises 404 if the newsletter doesn't exist"""
        fake_pk = 200000
        url = '/admin/newsletters/newsletter/%s/html/' % fake_pk
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 404)

    def test_newsletter_admin_text_raises_404(self):
        """Test newsletter text view on admin raises 404 if the newsletter doesn't exist"""
        fake_pk = 200000
        url = '/admin/newsletters/newsletter/%s/text/' % fake_pk
        response = self.client.get(url, follow=True)

        self.assertEqual(response.status_code, 404)

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

    def test_generate_newsletter(self):
        """Test generate newsletter admin view"""
        url = '/admin/newsletters/newsletter/new/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_generate_newsletter_action(self):
        """Test a newsletter is properly generated"""
        url = '/admin/newsletters/newsletter/new/'
        response = self.client.post(url, {
            'type': 10000,
            'start_date_0': '2020-10-22',
            'start_date_1': '00:00:00',
            'end_date_0': '2020-10-22',
            'end_date_1': '00:00:00',
        }, follow=True)

        self.assertEqual(response.status_code, 200)

    def test_send_newsletter_test_view(self):
        """Test send_test admin view"""
        url = '/admin/newsletters/newsletter/%s/send_test/' % self.newsletter.pk
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Newsletter: Send test email')
        self.assertContains(response, """<iframe src="../html/" frameborder="0" width="100%"  height="500"></iframe>""")
        self.assertContains(response, """<iframe src="../text/" width="100%"  height="500"></iframe>""")

    def test_send_newsletter_test(self):
        """Test send_test admin action"""
        url = '/admin/newsletters/newsletter/%s/send_test/' % self.newsletter.pk
        email = 'admin@newsletters.org'
        response = self.client.post(url, {
            'emails': email
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sent newsletter test emails to %s' % email)

    def test_send_newsletter_now_view(self):
        """Test send_now admin view"""
        # ensure that the newsletter hasn't been sent
        self.newsletter.send = None
        self.newsletter.save()
        url = '/admin/newsletters/newsletter/%s/send_now/' % self.newsletter.pk
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Newsletter: Send now')
        self.assertContains(response, """<iframe src="../html/" frameborder="0" width="100%"  height="500"></iframe>""")
        self.assertContains(response, """<iframe src="../text/" width="100%"  height="500"></iframe>""")

    def test_send_newsletter_now(self):
        # ensure that the newsletter hasn't been sent
        self.newsletter.send = None
        self.newsletter.save()
        """Test send_now admin action"""
        url = '/admin/newsletters/newsletter/%s/send_now/' % self.newsletter.pk
        response = self.client.post(url, {
            'send_now': True
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sent newsletter')

    def test_schedule_newsletter(self):
        """Test send_now admin action"""
        # ensure that the newsletter hasn't been sent
        self.newsletter.send = None
        self.newsletter.save()
        url = '/admin/newsletters/newsletter/%s/schedule/' % self.newsletter.pk
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Newsletter: Schedule for sending')
        self.assertContains(response, 'Schedule newsletter for sending:')
        self.assertContains(response, """<iframe src="../html/" frameborder="0" width="100%"  height="500"></iframe>""")
        self.assertContains(response, """<iframe src="../text/" width="100%"  height="500"></iframe>""")


    def test_schedule_newsletter(self):
        """Test send_now admin action"""
        url = '/admin/newsletters/newsletter/%s/schedule/' % self.newsletter.pk
        response = self.client.post(url, {
            'schedule': True
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Newsletter schedule to be sent at %s.' % self.newsletter.release_date)

    def test_unschedule_newsletter(self):
        """Test send_now admin action"""
        # ensure that the newsletter has been a scheduled status
        self.newsletter.scheduled_status = 'ON'
        self.newsletter.send = None
        self.newsletter.save()
        url = '/admin/newsletters/newsletter/%s/unschedule/' % self.newsletter.pk
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Newsletter: Cancel schedule')
        self.assertContains(response, 'Cancelling schedule for newsletter.')

    def test_unschedule_newsletter(self):
        """Test send_now admin action"""
        # ensure that the newsletter has been a scheduled status
        self.newsletter.scheduled_status = 'ON'
        self.newsletter.send = None
        self.newsletter.save()
        url = '/admin/newsletters/newsletter/%s/unschedule/' % self.newsletter.pk
        response = self.client.post(url, {
            'cancel_schedule': True
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cancelling schedule for newsletter.')
