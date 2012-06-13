# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names 
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE
#

"""
A Newsletter can be sent to many different distribution lists via Mailers. By default 
a NewsletterType must have at least one associated Mailer for a newsletter to be sent 
anywhere. A Mailer is defined by an admin who specifies which MailerPlugin to use, 
and any configuration values required by the MailerPlugin.

Currently the following MailerPlugins implementations are available:

  * Email - send the newsletter to a specific a list of email address.
  * Mailman list - send the newsletter to a mailman address, including unsubscribe and
  	subscription preferences links in the text.
  * MailChimp - send newsletter via MailChimp API.
 
A MailerPlugin must as a minimum support the following methods/properties:

  * ``name'' - Human readable name for the MailerPlugin
  * ``send_test( newsletter, emails )'' - Send a test version of the newsletters to the specified 
    list of email addresses
  * ``send_now( newsletter )'' - Send the newsletter for real.
  
Newsletters going to mailing lists must normally include instructions on how to unsubscribe. 
Since this differs from list to list, the newsletters sent to different lists cannot be 
identical. The method ``get_mailer_context'' allows the MailerPlugin to provide extra context
variables to the Newsletter template when being rendered. By default the following variables
are available:

  * ``unsubscribe_link''
  * ``preferences_link'' 
  * ``browser_link'' 

Each mailer plugin can override the ``get_mailer_context'' to provide their own context
variables for the templates.

The MailerPlugin should also specify names and types of any parameters that an admin
user may need to specify - e.g. the Mailman plugin needs the list's info URL to be specified.
The parameters are stored in MailerParameter, and are automatically created by the Mailer model.

----
"""

from django.core.mail import EmailMultiAlternatives

class MailerPlugin():
	"""
	Interface for mailer implementations.
	"""
	name = ''
	parameters = []
	
	def __init__( self, params ):
		"""
		Any parameters defined in ``MailerPlugin.parameters'' will be passed to the plugin via
		the params. The values of these parameters are configurable via the admin interface.
		"""
		pass
	
	def on_scheduled( self, newsletter ):
		"""
		Mailer plugins are notified when a newsletter is scheduled
		for sending. This allows plugins to do any preparations
		prior to sending if needed.
		
		.. note:: 
		
			The mailer plugins should NOT use their own scheduling 
			feature. send_now() will be called the right time to for all mailers
			to send the newsletter.
		"""
		pass
	
	def on_unscheduled( self, newsletter ):
		"""
		Mailer plugins are notified when a newsletter is unscheduled
		for sending. This allows plugins to do any cleanup needed when
		a scheduled newsletter is cancelled.
		"""
		pass
	
	def send_now( self, newsletter ):
		"""
		When invoked this method should send the newsletter immediately
		"""
		raise NotImplementedError
	
	def send_test( self, newsletter, emails ):
		"""
		When invoked this method should send a test version of the newsletter
		to the provided list of email addresses.
		"""
		raise NotImplementedError
	
	@classmethod
	def get_class_path( cls ):
		return "%s.%s" % ( cls.__module__, cls.__name__ )
	
	def get_mailer_context( self ):
		return {
			'unsubscribe_link' : '',
			'preferences_link' : '', 
			'browser_link' : '', 
		}


class EmailMailerPlugin( MailerPlugin ):
	"""
	Mailer implementation that will send the newsletter to a predefined
	list of email addresses (which could be e.g. a mailing list). 
	
	It does however not included any unsubscribe links or similar. The class
	can be used as base class for other MailerPlugins that works by sending 
	an email. Typically the derived class would just need to specifiy
	``name'', ``parameters'', ``__init__'' and ``'get_mailer_context()'.
	
	See MailmanMailerPlugin for an example. 
	"""
	name = 'Standard mailer'
	parameters = [ ( 'emails', 'Comma separated list of emails to send to.', 'str' ) ]

	def __init__( self, params ):
		try:
			self._to_emails = [x.strip() for x in params['emails'].split()]
		except KeyError:
			raise Exception( "Parameter 'emails' is missing" )

	def _send( self, newsletter, emails ):
		"""
		Send combined HTML and plain text email.
		"""
		data = newsletter.render( self.get_mailer_context(), store=False )
		
		from_email = '%s <%s>' % ( newsletter.from_name, newsletter.from_email )
		msg = EmailMultiAlternatives( data['subject'], data['text'], from_email, emails )
		msg.attach_alternative( data['html'], "text/html" )
		msg.send()


	def send_now( self, newsletter ):
		self._send( newsletter, self._to_emails )

	def send_test( self, newsletter, emails ):
		self._send( newsletter, emails )
		
	def get_mailer_context( self ):
		return {
			'unsubscribe_link' : '',
			'preferences_link' : '', 
			'browser_link' : '',
			'is_email_mailer' : True, 
		}
		
	
class MailmanMailerPlugin( EmailMailerPlugin ):
	"""
	Mailer implementation that sends a newsletter to an email address (usually a Mailman list), 
	and includes a unsubscribe and preferences link specified by the admin user.
	"""
	name = 'Mailman mailer'
	parameters = [ 
		( 'emails', 'Comma separated list of mailman list emails to send to.', 'str' ),
		( 'listinfo_url', 'URL to the listinfo mailman page', 'str' ),
	]
	
	def __init__( self, params ):
		try:
			self._to_emails = [x.strip() for x in params['emails'].split()]
		except KeyError:
			raise Exception( "Parameter 'emails' is missing" )
		try:
			self.listinfo_url = params['listinfo_url'].strip()
		except KeyError:
			raise Exception( "Parameter 'listinfo_url' is missing" )
	
	def get_mailer_context(self):
		return {
			'unsubscribe_link' : self.listinfo_url,
			'preferences_link' : self.listinfo_url, 
			'browser_link' : '',
			'is_mailman_mailer' : True,
		}

		
class MailChimpMailerPlugin( MailerPlugin ):
	"""
	Mailer implementation that will send the newsletter via MailChimp.
	It requires that the djangoplicity.mailinglists application has also been
	installed and that the MailChimp list have been defined.
	
	MailChimp have some length limits on subjects (150 chars) and campaign titles (100) so
	the plugin will chop off the values if they are too long. 
	
	HTML link tracking and opens tracking are enabled and is currently not configurable.
	
	When a newsletter is scheduled for sending it will be uploaded immediately to MailChimp, 
	however just before sending it will be uploaded again.  
	"""
	name = 'MailChimp mailer'
	parameters = [ 
		( 'list_id', 'MailChimp list id - must be defined in djangoplicity.', 'str' ),
		( 'enable_browser_link', "Enable 'view in browser' link", 'bool' ), 
	]

	def __init__( self, params ):
		try:
			list_id = params['list_id'].strip()
		except KeyError:
			raise Exception( "Parameter 'list_id' is missing" )
		try:
			self.enable_browser_link = params['enable_browser_link']
		except KeyError:
			raise Exception( "Parameter 'enable_browser_link' is missing" )
		
		from djangoplicity.mailinglists.models import MailChimpList
		self.ml = MailChimpList.objects.get( list_id=list_id )
		
	def _chop( self, value, limit ):
		"""
		Chop off parts of a string if needed to ensure
		its smaller than a maximum length.
		"""
		if len(value) >= limit-2:
			return "%s..." % value[:limit-5]
		else:
			return value
	
	def _update_campaign( self, nl, campaign_id ):
		"""
		Update an existing campaign in MailChimp.
		"""
		campaigns = self.ml.connection.campaigns( filters={ 'list_id' : self.ml.list_id, 'campaign_id' : campaign_id } )
		
		if 'total' in campaigns and campaigns['total'] > 0:
			vals = []
			vals.append( self.ml.connection.campaignUpdate( cid=campaign_id, name='subject', value=self._chop( nl.subject, 150 ) ) )
			vals.append( self.ml.connection.campaignUpdate( cid=campaign_id, name='from_email', value=nl.from_email ) )
			vals.append( self.ml.connection.campaignUpdate( cid=campaign_id, name='from_name', value=nl.from_name ) )
			vals.append( self.ml.connection.campaignUpdate( cid=campaign_id, name='title', value=self._chop( nl.subject, 100 ) ) )
			vals.append( self.ml.connection.campaignUpdate( cid=campaign_id, name='content', value={ 'html' : nl.html, 'text' : nl.text } ) )

			if False in vals:
				raise Exception( "Couldn't update campaign" )
			return ( campaign_id, False )
		else:
			return ( self._create_campaign( nl ), True )

	def _create_campaign( self, nl ):
		"""
		Create a new campaign in MailChimp
		"""
		val = self.ml.connection.campaignCreate(
			type = 'regular',
			options = {
				'list_id' : self.ml.list_id,
				'subject' : self._chop( nl.subject, 150 ),
				'from_email' : nl.from_email,
				'from_name' : nl.from_name,
				'tracking' : { 'opens' : True, 'html_clicks' : True, 'text_clicks' : False },
				'title' : self._chop( nl.subject, 100 ),
				'authenticate' : True,
				'auto_footer' : False,
				'inline_css' : True,
				'fb_comments' : True,
			},
			content = {
				'html' : nl.html,
				'text' : nl.text,
			}
		 )

		if 'error' in val:
			raise Exception("MailChimp could not create the campaign, error %d: '%s'." % (val['code'], val['error']))
		return val
	
	def _upload_newsletter( self, newsletter ):
		"""
		Uploadd a newsletter into MailChimp, and record the MailChimp campaign id. 
		"""
		from djangoplicity.newsletters.models import MailChimpCampaign
		
		newsletter.render( self.get_mailer_context() )
		
		( info, created ) = MailChimpCampaign.objects.get_or_create( newsletter=newsletter, list_id=self.ml.list_id )
		
		if not created and info.campaign_id:
			( info.campaign_id, touched ) = self._update_campaign( newsletter, info.campaign_id )
			if touched:
				info.save()
		else:
			info.campaign_id = self._create_campaign( newsletter )
			info.save()
		
		return info
	
	def get_mailer_context(self):
		return {
			'unsubscribe_link' : '*|UNSUB|*', # MailChimp will automatically replace the tag *|...|*-tags with a lists unsubscribe link etc. 
			'preferences_link' : '*|UPDATE_PROFILE|*', 
			'browser_link' : '*|ARCHIVE|*' if self.enable_browser_link else '',
			'is_mailchimp_mailer' : True,
		}

	def on_scheduled( self, newsletter ):
		"""
		Notification that a newsletter was scheduled for sending.
		"""
		info = self._upload_newsletter( newsletter )

	def send_now( self, newsletter ):
		"""
		Send newsletter now.
		"""
		info = self._upload_newsletter( newsletter )
		if not self.ml.connection.campaignSendNow( cid=info.campaign_id ):
			raise Exception("MailChimp could not send newsletter.")

	def send_test( self, newsletter, emails ):
		"""
		Send a test email for this newsletter
		"""
		info = self._upload_newsletter( newsletter )
		if not self.ml.connection.campaignSendTest( cid=info.campaign_id, test_emails=emails ):
			raise Exception("MailChimp could not send test email.")

	
