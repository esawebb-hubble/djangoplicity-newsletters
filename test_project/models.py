from django.db import models
from djangoplicity.newsletters.mailers import MailmanMailerPlugin, MailChimpMailerPlugin

class SimpleMailer( MailmanMailerPlugin ):
    name = 'Standard mailer'

    mailer_parameters = [
            ('name', 'list name', 'str'),
            ( 'password', 'Admin password for list', 'str' ),
            ( 'somenum', 'Some num', 'int' ),
        ]
    abstract = True

    def __init__(self, *args, **kwargs):
        pass

class SimpleMailChimpMailerPlugin( MailChimpMailerPlugin ):
    name = 'MailChimp mailer'

    parameters = [
        ('list_id', '7727d019e9', 'str'),
        ('enable_browser_link', False, 'bool'),
    ]
    abstract = True

    def __init__(self, parameters):
        MailChimpMailerPlugin.__init__(self, parameters)