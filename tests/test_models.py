from django.core.exceptions import ValidationError
from django.test import TestCase
from djangoplicity.mailinglists.models import BadEmailAddress, List, Subscription, Subscriber


class TestModels(TestCase):
    LIST_NAME = 'esoepo-monitoring'
    LIST_PASSWORD = 'ohsiechu'
    LIST_BASEURL = 'http://www.eso.org/lists'

    def test_bad_email_address_str(self):
        """Test bad email address string representation"""
        bea = BadEmailAddress(email='test@eso.org')
        self.assertEqual(str(bea), 'test@eso.org')

    def test_subscriber_str(self):
        """Test subscriber string representation"""
        subscriber = Subscriber(email='test@eso.org')
        self.assertEqual(str(subscriber), 'test@eso.org')

    def test_list_str(self):
        """Test list string representation"""
        list = List(base_url=self.LIST_BASEURL, name=self.LIST_NAME, password=self.LIST_PASSWORD)
        self.assertEqual(str(list), self.LIST_NAME)

    def test_subscription_str(self):
        """Test subscription string representation"""
        subscriber = Subscriber(email='test@eso.org')
        list = List(base_url=self.LIST_BASEURL, name=self.LIST_NAME, password=self.LIST_PASSWORD)
        subscription = Subscription(subscriber=subscriber, list=list)

        self.assertEqual(str(subscription), 'test@eso.org subscribed to %s' % self.LIST_NAME)
