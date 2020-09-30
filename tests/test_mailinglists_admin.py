from datetime import datetime
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from test_project.settings import NEWSLETTERS_MAILCHIMP_API_KEY, NEWSLETTERS_MAILCHIMP_LIST_ID

TEST_API_KEY = NEWSLETTERS_MAILCHIMP_API_KEY
TEST_LIST_ID = NEWSLETTERS_MAILCHIMP_LIST_ID


class AdminSiteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@hubble.org',
            password='password123'
        )
        self.client.force_login(self.admin_user)

    def test_admin_pages_for_models(self):
        """Test that pages for models in admin are properly generated"""
        models = ['bademailaddress', 'subscriber', 'subscription', 'list', 'mailchimplist', 'mailchimplisttoken']
        for model in models:
            url = '/admin/mailinglists/%s/' % model
            res = self.client.get(url)

            self.assertEqual(res.status_code, 200)

    def test_add_list_page(self):
        """Test that mailchimp list add page contains all inline forms"""
        url = '/admin/mailinglists/mailchimplist/add/'
        res = self.client.get(url)

        self.assertEquals(res.status_code, 200)
        self.assertContains(res, "List information")
        self.assertContains(res, "Following information is configured in MailChimp administration interface.")
        # test that contains inline admins
        self.assertContains(res, "Mailchimp merge fields")
        self.assertContains(res, "Mail chimp groups")
        self.assertContains(res, "Mail chimp groupings")
        self.assertContains(res, "Mailchimp merge field mappings")
        self.assertContains(res, "Group mappings")

    def test_action_install_webhooks(self):
        from djangoplicity.mailinglists.models import MailChimpList
        list = MailChimpList.objects.create(api_key=TEST_API_KEY, list_id=TEST_LIST_ID)

        url = '/admin/mailinglists/mailchimplist/'
        data = {'action': 'action_install_webhooks', '_selected_action': [list.pk]}
        res = self.client.post(url, data, follow=True)

        self.assertEquals(res.status_code, 200)
        self.assertContains(res, "Installing webhooks for lists %s" % list.name)

    def test_action_update_info(self):
        from djangoplicity.mailinglists.models import MailChimpList
        list = MailChimpList.objects.create(api_key=TEST_API_KEY, list_id=TEST_LIST_ID)

        url = '/admin/mailinglists/mailchimplist/'
        data = {'action': 'action_update_info', '_selected_action': [list.pk]}
        res = self.client.post(url, data, follow=True)

        self.assertEquals(res.status_code, 200)
        self.assertContains(res, "Updating statistics from lists %s." % list.name)
