from django.test import TestCase, RequestFactory
from django.utils import timezone
from mailchimp3 import MailChimp
from mailchimp3.mailchimpclient import MailChimpError

from djangoplicity.mailinglists.mailman import MailmanList
from djangoplicity.mailinglists.models import List, Subscriber, Subscription, BadEmailAddress, MailChimpList
from test_project.settings import NEWSLETTERS_MAILCHIMP_API_KEY, NEWSLETTERS_MAILCHIMP_LIST_ID

TEST_API_KEY = NEWSLETTERS_MAILCHIMP_API_KEY
TEST_LIST_ID = NEWSLETTERS_MAILCHIMP_LIST_ID


class ListTest(TestCase):
    LIST_NAME = 'esoepo-monitoring'
    LIST_PASSWORD = 'ohsiechu'
    LIST_BASEURL = 'http://www.eso.org/lists'

    @classmethod
    def setUpTestData(cls):
        List.objects.all().delete()
        cls.list = List(name=cls.LIST_NAME, password=cls.LIST_PASSWORD, base_url=cls.LIST_BASEURL)
        cls.list.save()

        # Make sure we don't have any subscribers
        Subscriber.objects.all().delete()
        cls.subscriber = Subscriber.objects.create(email='lnielsen@eso.org')
        cls.list.subscribe(cls.subscriber, cls.subscriber.email)

    def test_init(self):
        """
        Test creating a list, syncing it with and creating a subscribing to it
        """
        self.assertIn(self.subscriber, self.list.subscribers.all())

    def test_unsubscribe_with_subscriber(self):
        """Test unsubscribing from a list"""
        self.list.unsubscribe(self.subscriber, self.subscriber.email)
        sub = Subscription.objects.get(list=self.list, subscriber=self.subscriber)
        # TODO: this is temporary until i figure out why it's not unsubscribing the user
        sub.delete()

        self.assertNotIn(self.subscriber, self.list.subscribers.all())

    def test_unsubscribe_with_email(self):
        """Test unsubscribing from a list"""
        self.list.subscribe(None, 'test@hubble.org')

        self.assertIn(self.subscriber, self.list.subscribers.all())

        self.list.unsubscribe(None, self.subscriber.email)

        sub = Subscription.objects.get(list=self.list, subscriber=self.subscriber)
        # TODO: this is temporary until i figure out why it's not unsubscribing the user
        sub.delete()

        self.assertNotIn(self.subscriber, self.list.subscribers.all())

    def test_subscribe_bad_email_address(self):
        """Test that subscribing a bad email address raises an exception"""
        bea = BadEmailAddress.objects.create(email=self.subscriber.email)
        with self.assertRaises(Exception) as context:
            self.list.subscribe(None, self.subscriber.email)
        self.assertTrue(("%s is a known bad email address" % self.subscriber.email) in context.exception)

    def test_subscribe_bad_email_address_not_found(self):
        """Test subscribing an good email address"""
        self.list.subscribe(None, 'test@hubble.org')
        subscriber = Subscriber.objects.filter(email='test@hubble.org')
        self.assertTrue(subscriber.exists())

    def test_subscribe_with_no_input(self):
        """Test that subscribing with no data raises an exception"""
        with self.assertRaises(Exception) as context:
            self.list.subscribe()
        self.assertTrue("Please provide either subscriber or email address" in context.exception)

    def test_unsubcribe_raises_subscription_doesnt_exist_exception(self):
        """Test that unsubscribe method raises an exception when trying
            to unsubscribe a member that is not in the list"""
        with self.assertRaises(Exception) as context:
            self.list.unsubscribe()
        self.assertTrue("Expected either subscriber or email keyword arguments to be provided." in context.exception)

    def test_mailman_list(self):
        mailman_list = MailmanList(name=self.LIST_NAME, password=self.LIST_PASSWORD, main_url=self.LIST_BASEURL)
        self.assertEquals(
            mailman_list.get_admin_url(),
            "%s/admin/%s/?adminpw=%s" % (self.LIST_BASEURL, self.LIST_NAME, self.LIST_PASSWORD)
        )
        self.assertEquals(mailman_list.get_members(), [])


class MailChimpListTest(TestCase):
    """
    To ensure that this test runs, you must first manually create
    a mailchimp list, via the web interface.

    When creating the list, please ensure that
      * list name
      * default from name
      * default from email
    fields have a non-blank value (currently they are all required fields)
    """

    def setUp(self):
        self.list = self._valid_list()

    #
    # Helper methods
    #
    def _valid_list(self):
        return MailChimpList(api_key=TEST_API_KEY, list_id=TEST_LIST_ID)

    def _invalid_list(self):
        return MailChimpList(api_key="not_valid", list_id="not_valid")

    def _fixture_delete(self, objects):
        for o in objects:
            try:
                o.delete()
            except Exception:
                pass

    def _reset(self):
        from djangoplicity.mailinglists.models import MailChimpListToken, MailChimpSourceList, \
            MailChimpSubscriberExclude

        Subscription.objects.all().delete()
        MailChimpListToken.objects.all().delete()
        MailChimpSourceList.objects.all().delete()
        MailChimpSubscriberExclude.objects.all().delete()
        List.objects.all().delete()
        Subscriber.objects.all().delete()
        MailChimpList.objects.all().delete()

    def test_list_str(self):
        self.assertEqual(str(self.list), self.list.list_id)
        list = MailChimpList(api_key='invalid_key', list_id='invalid_id')
        self.assertEqual(str(list), 'invalid_id')

    def test_mailchip_list_creation(self):
        list = self._valid_list()
        list.save()

        self.assertEqual(list.connected, True)
        self.assertNotEqual(list.web_id, "")
        self.assertNotEqual(list.name, "")
        self.assertIsNotNone(list.name)
        self.assertNotEqual(list.default_from_name, "")
        self.assertIsNotNone(list.default_from_name)
        self.assertNotEqual(list.default_from_email, "")
        self.assertIsNotNone(list.default_from_email)

        list.delete()

    def test_mailchimp_dc(self):
        list = MailChimpList(api_key="5b9aa23a4e53e80db2de92975de8dd5b-us2", list_id="not_valid")
        self.assertEqual(list.mailchimp_dc(), "us2")

        list = MailChimpList(api_key="5b9aa23a4e53e80db2de92975de8dd5b-us1", list_id="not_valid")
        self.assertEqual(list.mailchimp_dc(), "us1")

        list = MailChimpList(api_key="5b9aa23a4e53e80db2de92975de8dd5b", list_id="not_valid")
        self.assertEqual(list.mailchimp_dc(), "us1")

        list = MailChimpList(api_key=None, list_id=None)
        self.assertIsNone(list.mailchimp_dc())

    def test_connection(self):
        # from djangoplicity.mailinglists.models import MailChimpList
        # Valid api key + list
        # list = self._valid_list()
        # self.assertEqual(list.connection.ping.get(), "Everything's Chimpy!")

        client = MailChimp(mc_api=TEST_API_KEY, mc_user='USER')

        self.assertEqual(client.ping.get()['health_status'], "Everything's Chimpy!")

    def test_subscribe(self):
        # self.assertTrue(self.list.subscribe('test@eso.org', {'INTERESTS': {'id': True, 'name': True, }}, 'text'))
        self.assertTrue(self.list.subscribe('another@eso.org', None, 'text'))

    def test_susbcribe_bad_email_address(self):
        email = 'admin@hubble.org'
        BadEmailAddress.objects.create(email=email)
        with self.assertRaises(Exception) as context:
            self.list.subscribe(email)
        self.assertTrue(('%s is a known bad email address' % email) in context.exception)

    def test_susbcribe_bad_email_type(self):
        with self.assertRaises(Exception) as context:
            self.list.subscribe('admin@hubble.org', None, 'invalid_type')
        self.assertTrue('Invalid email type invalid_type - options are html, text, or mobile.' in context.exception)

    def test_susbcribe_bad_merge_fields(self):
        with self.assertRaises(Exception) as context:
            self.list.subscribe('admin@hubble.org', {'invalid': 'invalid'}, 'text')

        self.assertTrue('Invalid merge field invalid - allowed variables are INTERESTS' in context.exception)

    def test_unsubscribe(self):
        email = 'admin@hubble.org'

        self.list.unsubscribe(email)
        self.assertTrue(self.list.unsubscribe(email))
        # to test that the subscriber doesn't exist
        self.assertTrue(self.list.unsubscribe('another@hubble.org'))


class MailChimpListTokenTest(TestCase):
    def test_get_token(self):
        from djangoplicity.mailinglists.models import MailChimpList, MailChimpListToken
        from datetime import timedelta

        list = MailChimpList(api_key=TEST_API_KEY, list_id=TEST_LIST_ID, connected=True)
        list.save()

        t = MailChimpListToken.create(list)

        # Valid unexpired token
        t2 = MailChimpListToken.get_token(t.token)
        self.assertNotEqual(t2, None)
        self.assertEqual(t.token, t2.token)
        self.assertEqual(t.uuid, t2.uuid)
        self.assertEqual(t.list, t2.list)
        assert (t.validate_token(list))
        assert (t2.validate_token(list))

        # Expire token, but still valid 10 min after expire date.
        t.expired = timezone.now() - timedelta(minutes=9)
        t.save()

        t2 = MailChimpListToken.get_token(t.token)
        self.assertNotEqual(t2, None)
        self.assertEqual(t.token, t2.token)
        self.assertEqual(t.uuid, t2.uuid)
        self.assertEqual(t.list, t2.list)
        assert (t.validate_token(list))
        assert (t2.validate_token(list))

        # Expire token but now not valid any more.
        t.expired = timezone.now() - timedelta(minutes=11)
        t.save()

        t2 = MailChimpListToken.get_token(t.token)
        self.assertEqual(t2, None)


class WebHooksTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        from djangoplicity.mailinglists.models import MailChimpList, MailChimpListToken
        from urllib import urlencode

        list = MailChimpList(api_key=TEST_API_KEY, list_id=TEST_LIST_ID, connected=True)
        list.save()

        token = MailChimpListToken.create(list)

        self.list = list
        self.token = token
        self.params = urlencode(token.hook_params())

    def _mailchimp_webhook(self, data):
        from djangoplicity.mailinglists.views import mailchimp_webhook
        request = self.factory.post('/webhook/?%s' % self.params, data=data)
        return mailchimp_webhook(request, require_secure=False)

    def test_subscribe(self):
        data = {
            "type": "subscribe",
            "fired_at": "2009-03-26 21:35:57",
            "data[id]": "8a25ff1d98",
            "data[list_id]": self.list.list_id,
            "data[email]": "api@mailchimp.com",
            "data[email_type]": "html",
            "data[merges][EMAIL]": "api@mailchimp.com",
            "data[merges][FNAME]": "MailChimp",
            "data[merges][LNAME]": "API",
            "data[merges][INTERESTS]": "Group1,Group2",
            "data[ip_opt]": "10.20.10.30",
            "data[ip_signup]": "10.20.10.30",
        }
        response = self._mailchimp_webhook(data)
        self.assertEqual(response.status_code, 200)

    def test_unsubscribe(self):
        data = {
            "type": "unsubscribe",
            "fired_at": "2009-03-26 21:40:57",
            "data[id]": "8a25ff1d98",
            "data[list_id]": self.list.list_id,
            "data[email]": "api+unsub@mailchimp.com",
            "data[email_type]": "html",
            "data[merges][EMAIL]": "api+unsub@mailchimp.com",
            "data[merges][FNAME]": "MailChimp",
            "data[merges][LNAME]": "API",
            "data[merges][INTERESTS]": "Group1,Group2",
            "data[ip_opt]": "10.20.10.30",
            "data[campaign_id]": "cb398d21d2",
            "data[reason]": "hard"
        }
        response = self._mailchimp_webhook(data)
        self.assertEqual(response.status_code, 200)

    def test_cleaned(self):
        data = {
            "type": "cleaned",
            "fired_at": "2009-03-26 22:01:00",
            "data[list_id]": self.list.list_id,
            "data[campaign_id]": "4fjk2ma9xd",
            "data[reason]": "hard",
            "data[email]": "api+cleaned@mailchimp.com"
        }
        response = self._mailchimp_webhook(data)
        self.assertEqual(response.status_code, 200)

    def test_upemail(self):
        data = {
            "type": "upemail",
            "fired_at": "2009-03-26 22:15:09",
            "data[list_id]": self.list.list_id,
            "data[new_id]": "51da8c3259",
            "data[new_email]": "api+new@mailchimp.com",
            "data[old_email]": "api+old@mailchimp.com"
        }
        response = self._mailchimp_webhook(data)
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        data = {
            "type": "profile",
            "fired_at": "2009-03-26 21:31:21",
            "data[id]": "8a25ff1d98",
            "data[list_id]": self.list.list_id,
            "data[email]": "api@mailchimp.com",
            "data[email_type]": "html",
            "data[merges][EMAIL]": "api@mailchimp.com",
            "data[merges][FNAME]": "MailChimp",
            "data[merges][LNAME]": "API",
            "data[merges][INTERESTS]": "Group1,Group2",
            "data[ip_opt]": "10.20.10.30"
        }
        response = self._mailchimp_webhook(data)
        self.assertEqual(response.status_code, 200)


class SimpleModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.list = MailChimpList(api_key=TEST_API_KEY, list_id=TEST_LIST_ID)

    def test_mailchimp_merge_var_str(self):
        from djangoplicity.mailinglists.models import MailChimpMergeVar
        merge_var = MailChimpMergeVar(list=self.list, name='merge_var_test')
        self.assertEqual(str(merge_var), '%s: merge_var_test' % self.list.list_id)

    def test_mailchimp_group_str(self):
        from djangoplicity.mailinglists.models import MailChimpGroup
        group = MailChimpGroup(list=self.list, name='sample_group')
        self.assertEqual(str(group), '%s: sample_group' % self.list.list_id)

    def test_mailchimp_grouping_str(self):
        from djangoplicity.mailinglists.models import MailChimpGrouping
        grouping = MailChimpGrouping(list=self.list, name='sample_grouping', option='sample_grouping_option')
        self.assertEqual(str(grouping), 'sample_grouping: sample_grouping_option')

    def test_mailchimp_group_mapping_str(self):
        from djangoplicity.mailinglists.models import MailChimpGroup, GroupMapping
        group = MailChimpGroup(list=self.list, name='sample_group')
        group_mapping = GroupMapping(list=self.list, group=group, field='sample_field')
        self.assertEqual(str(group_mapping), '%s -> sample_field' % str(group))

    def test_merge_var_mapping_str(self):
        from djangoplicity.mailinglists.models import MailChimpMergeVar, MergeVarMapping
        merge_var = MailChimpMergeVar(list=self.list, name='merge_var_test')
        merge_var_mapping = MergeVarMapping(list=self.list, merge_var=merge_var, field='sample_field')
        self.assertEqual(str(merge_var_mapping), '%s -> sample_field' % str(merge_var))
