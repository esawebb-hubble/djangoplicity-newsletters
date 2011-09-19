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

from django.core.mail import EmailMultiAlternatives

class CampaignUploadError( Exception ):
	pass

class MailerPlugin():
	"""
	Interface for mailer implementations
	"""
	name = ''
	parameters = []
	
	def __init__( self, params ):
		pass
	
	def send_now( self, newsletter ):
		"""
		When invoked this method should send the newsletter immediately
		"""
		raise NotImplementedError
	
	def send_test( self, newsletter, emails ):
		raise NotImplementedError
	
	def schedule( self, newsletter, delivery ):
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
		Send combined html and plain text email.
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
	Mailer implementation that will send the newsletter to a predefined
	list of email addresses (which could be e.g. a mailing list). 
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

	
	def _update_campaign( self, nl, campaign_id ):
		"""
		Update an existing campaign in MailChimp
		"""
		campaigns = self.ml.connection.campaigns( filters={ 'list_id' : self.ml.list_id, 'campaign_id' : campaign_id } )
		
		if 'total' in campaigns and campaigns['total'] > 0:
			vals = []
			vals.append( self.ml.connection.campaignUpdate( cid = campaign_id, name = 'subject', value = nl.subject[:150] ) )
			vals.append( self.ml.connection.campaignUpdate( cid = campaign_id, name = 'from_email', value = nl.from_email ) )
			vals.append( self.ml.connection.campaignUpdate( cid = campaign_id, name = 'from_name', value = nl.from_name ) )
			vals.append( self.ml.connection.campaignUpdate( cid = campaign_id, name = 'title', value = nl.subject[:100] ) )
			vals.append( self.ml.connection.campaignUpdate( cid = campaign_id, name = 'content', value = { 'html' : nl.html, 'text' : nl.text } ) )
			if False in vals:
				raise Exception( "Could update campaign" )
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
				'subject' : nl.subject[:150],
				'title' : nl.subject[:100],
				'from_email' : nl.from_email,
				'from_name' : nl.from_name,
				'tracking' : { 'opens' : True, 'html_clicks' : True, 'text_clicks' : False },
				'title' : nl.subject,
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
		return val
	
	def _upload_newsletter( self, newsletter ):
		"""
		Send combined html and plain text email.
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
			'unsubscribe_link' : '*|UNSUB|*',
			'preferences_link' : '*|UPDATE_PROFILE|*', 
			'browser_link' : '*|ARCHIVE|*' if self.enable_browser_link else '',
			'is_mailchimp_mailer' : True,
		}

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

	