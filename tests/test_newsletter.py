from django.test import TestCase
from djangoplicity.newsletters.models import Mailer, MailerParameter, MailerLog, make_nl_id, Newsletter, NewsletterType, MailChimpCampaign, Language, NewsletterLanguage, NewsletterGenerator, DataSourceSelector
from djangoplicity.newsletters.mailers import MailChimpMailerPlugin, MailmanMailerPlugin, EmailMailerPlugin
from test_project.models import SimpleMailer, SimpleMailChimpMailerPlugin
from django.conf import settings

from djangoplicity.mailinglists.models import MailChimpList

from test_project.settings import NEWSLETTERS_MAILCHIMP_API_KEY, NEWSLETTERS_MAILCHIMP_LIST_ID

class MailerTestCase(TestCase):

    TEST_API_KEY = NEWSLETTERS_MAILCHIMP_API_KEY
    TEST_LIST_ID = NEWSLETTERS_MAILCHIMP_LIST_ID

    #
    # Helper methods
    #
    def _valid_list( self ):
        MailChimpList.objects.all().delete()
        l = MailChimpList( api_key=self.TEST_API_KEY, list_id=self.TEST_LIST_ID, synchronize=True )
        l.save()
        return l
    
    def createDataSourceSelector(self):
        DataSourceSelector.objects.all().delete()
        ds = DataSourceSelector(
            name='Embargo date end start_date',
            filter='I',
            field='embargo_date',
            match='gt',
            value='%(start_date)s',
            type='str'
        )
        ds.save()
        return ds
    
    def createNewMailer(self):
        Mailer.objects.all().delete()
        m = Mailer(plugin='djangoplicity.newsletters.mailers.MailChimpMailerPlugin', name='Simple Mailer')
        m.register_plugin(MailChimpMailerPlugin)
        m.save()
        return m
    
    def createNewMailerTest(self):
        Mailer.objects.all().delete()
        m = Mailer(plugin='test_project.models.SimpleMailer', name='Simple Mailer')
        m.register_plugin(SimpleMailer)
        m.save()
        return m
    
    def createNewMailerParameterTest(self, mailer):
        MailerParameter.objects.all().delete()
        p = MailerParameter.objects.create(mailer=mailer ,name='test', value='value test')
        p.save()
        return p
    
    def createNewMailerParameterListId(self, mailer):
        MailerParameter.objects.all().delete()
        p1 = MailerParameter.objects.create(mailer=mailer ,name='list_id', value='7727d019e9')
        p1.save()
        return p1
    
    def createNewMailerParameterEnable_browser_link(self, mailer):
        # MailerParameter.objects.all().delete()
        p = MailerParameter.objects.create(mailer=mailer ,name='enable_browser_link', value=True)
        p.save()
        return p
    
    def createNewsletterLanguage(self, newsletter_type, language):
        NewsletterLanguage.objects.all().delete()
        nll = NewsletterLanguage.objects.create(
            newsletter_type = newsletter_type,
            language = language
        )
        nll.save()
        return nll
    
    def createNewsletterType(self):
        NewsletterType.objects.all().delete()
        l = self.createLanguage()
        m = self.createNewMailer()
        # print Language.objects.all()
        nt = NewsletterType.objects.create(
            id=1,
            name='NewsletterType Test',
            slug='slug-test',
            default_from_name='test',
            default_from_email='test@test.com',
            # languages=l
        )
        nll = self.createNewsletterLanguage(nt, l)
        return nt
    
    def createNewsletterTypeOther(self):
        NewsletterType.objects.all().delete()
        l = self.createLanguage()
        # print Language.objects.all()
        nt = NewsletterType.objects.create(
            id=1,
            name='NewsletterType Test',
            slug='newsletterType-test',
            default_from_name='test',
            default_from_email='test@test.com',
            # languages=l
        )
        nll = self.createNewsletterLanguage(nt, l)
        nt.save()
        return nt
    
    def createNewsletter(self, newsletterType):
        Newsletter.objects.all().delete()
        n = Newsletter.objects.create(
            id='1',
            type=newsletterType
        )
        n.save()
        return n
    
    def createLanguage(self):
        Language.objects.all().delete()
        l = Language.objects.create(
            lang = settings.LANGUAGE_CODE
        )
        l.save()
        return l

    def test_list_mailer(self):
        m = self.createNewMailer()
        list_choices = m.get_plugin_choices()
        list_test = [
            (MailChimpMailerPlugin.get_class_path(), MailChimpMailerPlugin.name),
            (MailmanMailerPlugin.get_class_path(), MailmanMailerPlugin.name),
            (EmailMailerPlugin.get_class_path(), EmailMailerPlugin.name),
            (SimpleMailer.get_class_path(), SimpleMailer.name),
        ]
        # print list_choices
        self.assertEquals(list_choices, list_test )

    def test_get_class_registered(self):
        m = self.createNewMailer()
        self.assertEquals(m.get_plugincls(), MailChimpMailerPlugin)
    
    def test_get_plugin(self):
        m = self.createNewMailerTest()
        p = self.createNewMailerParameterTest(m)
        self.assertIsInstance(m.get_plugin(), SimpleMailer)
    
    def test_get_parameters(self):
        m = self.createNewMailer()
        p = self.createNewMailerParameterListId(m)
        self.assertEquals(m.get_parameters(), {u'list_id': u'7727d019e9'})

    def test_dispatch(self):
        a = self.createNewMailer()
        p = self.createNewMailerParameterListId(a)
        #self.assertTrue(SimpleAction.successful())
        a.post_save_handler()

    def test_get_value(self):
        a = self.createNewMailer()
        p = self.createNewMailerParameterListId(a)
        self.assertEquals(p.get_value(), u'7727d019e9')
    
    def test_create_mailerLog(self):
        a = MailerLog(plugin='djangoplicity.newsletters.mailers.MailChimpMailerPlugin', name='Simple action')
        self.assertEquals(a.name, u'Simple action')
    
    def test_get_class_path(self):
        a = self.createNewMailerTest()
        p = self.createNewMailerParameterTest(a)
        log = a.get_plugin()
        path = log.get_class_path()
        self.assertEquals(path, SimpleMailer.get_class_path())
    
    def test_get_id(self):
        a = self.createNewMailer()
        self.assertEquals(make_nl_id(), u'1')

    def test_on_scheduled(self):
        # l = self._valid_list()
        # sm = SimpleMailChimpMailerPlugin()
        a = self.createNewMailer()
        nlt = self.createNewsletterType()
        nl = self.createNewsletter(nlt)
        # print a.on_scheduled(nl)

    def test__unicode__(self):
        m = self.createNewMailer()
        self.assertEquals(m.__unicode__(), 'MailChimp mailer: Simple Mailer')
    
    def test_log_entry(self):
        m = self.createNewMailer()
        nlt = self.createNewsletterType()
        nl = self.createNewsletter(nlt)
        log = m._log_entry(nl)
        self.assertEquals(m.name, 'Simple Mailer')
    
    def test_send_test(self):
        m = self.createNewMailer()
        nlt = self.createNewsletterType()
        nl = self.createNewsletter(nlt)
        self.assertEquals(m.send_test(nl), None)

    def test_send_now(self):
        l = self._valid_list()
        m = self.createNewMailer()
        p1 = self.createNewMailerParameterListId(m)
        p2 = self.createNewMailerParameterEnable_browser_link(m)
        nlt = self.createNewsletterTypeOther()
        nlt.mailers.add(m)
        nlt.save()
        nl = self.createNewsletter(nlt)
        # print m.send_now(nl) 
        # print m.get_parameters()
    
    def test_get_generator(self):
        l = self._valid_list()
        m = self.createNewMailer()
        p1 = self.createNewMailerParameterListId(m)
        p2 = self.createNewMailerParameterEnable_browser_link(m)
        nlt = self.createNewsletterTypeOther()
        nlt.mailers.add(m)
        nlt.save()
        self.assertIsInstance(nlt.get_generator(), NewsletterGenerator)

    def test_get_absolute_url(self):
        l = self._valid_list()
        m = self.createNewMailer()
        p1 = self.createNewMailerParameterListId(m)
        p2 = self.createNewMailerParameterEnable_browser_link(m)
        nlt = self.createNewsletterTypeOther()
        nlt.mailers.add(m)
        nlt.save()
        self.assertEquals(nlt.get_absolute_url(), '/newsletters/newsletterType-test/')
    
    def test_get___unicode__(self):
        l = self._valid_list()
        m = self.createNewMailer()
        p1 = self.createNewMailerParameterListId(m)
        p2 = self.createNewMailerParameterEnable_browser_link(m)
        nlt = self.createNewsletterTypeOther()
        nlt.mailers.add(m)
        nlt.save()
        self.assertEquals(nlt.__unicode__(), 'NewsletterType Test')
    
    def test_schedule(self):
        l = self._valid_list()
        m = self.createNewMailer()
        p1 = self.createNewMailerParameterListId(m)
        p2 = self.createNewMailerParameterEnable_browser_link(m)
        nlt = self.createNewsletterType()
        nl = self.createNewsletter(nlt)
        # print nl._schedule(1)
        # self.assertEquals(m.send_test(nl), None)

    def test_get_absolute_url_newsletter(self):
        l = self._valid_list()
        m = self.createNewMailer()
        p1 = self.createNewMailerParameterListId(m)
        p2 = self.createNewMailerParameterEnable_browser_link(m)
        nlt = self.createNewsletterType()
        nl = self.createNewsletter(nlt)
        self.assertEquals(nl.get_absolute_url(), '/newsletters/slug-test/html/1/')
    
    def test_get_feed_data(self):
        ds = self.createDataSourceSelector()
        lan = self.createLanguage()
        l = self._valid_list()
        m = self.createNewMailer()
        p1 = self.createNewMailerParameterListId(m)
        p2 = self.createNewMailerParameterEnable_browser_link(m)
        nlt = self.createNewsletterType()
        nl = self.createNewsletter(nlt)
        self.assertEquals(nl.get_feed_data(), {})