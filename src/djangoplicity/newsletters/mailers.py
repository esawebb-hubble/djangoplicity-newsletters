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
from email import charset as Charset


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
			'unsubscribe_link': '',
			'preferences_link': '',
			'browser_link': '',
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

	def _send( self, newsletter, emails, test=False ):
		"""
		Send combined HTML and plain text email.
		"""
		data = newsletter.render( self.get_mailer_context(), store=False )

		from_email = '%s <%s>' % ( newsletter.from_name, newsletter.from_email )

		subject = data['subject']
		if test:
			subject = 'TEST - ' + subject

		# Mon Oct 14 16:11:03 CEST 2013 - Mathias Andre
		# Django 1.4 changed the default encoding from quoted-printable to 8bit
		# This can cause problem with HTML content where lines > 998 characters
		# end up cut arbitrarily by the mail server.
		# To fix this we force back quoted-printable
		Charset.add_charset('utf-8', Charset.SHORTEST, Charset.QP, 'utf-8')
		msg = EmailMultiAlternatives( subject, data['text'], from_email, emails )
		msg.attach_alternative( data['html'], "text/html" )
		msg.send()

	def send_now( self, newsletter ):
		self._send( newsletter, self._to_emails )

	def send_test( self, newsletter, emails ):
		self._send( newsletter, emails, test=True )

	def get_mailer_context( self ):
		return {
			'unsubscribe_link': '',
			'preferences_link': '',
			'browser_link': '',
			'is_email_mailer': True,
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
			'unsubscribe_link': self.listinfo_url,
			'preferences_link': self.listinfo_url,
			'browser_link': '',
			'is_mailman_mailer': True,
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
		#  Encode the string to utf otherwise Mailchimp might complain
		#  about the length of special characters,
		#  i.e.: Mailchimp counts '\xc3' as 4 characters instead of one
		#  We can't just encode the string in utf and then cut it as
		#  it might cut characters in the wrong place, so we do it char by char

		if len(value.encode('utf-8')) <= limit:
			return value

		while len(value.encode('utf-8')) > limit - 3:
			value = value[:-1]

		value = value + '...'
		return value.encode('utf-8')

	def _set_segment( self, campaign, language, languages ):
		"""
		Update the campaign segment to only send to members of the
		given language
		"""
		# If the newsletter doesn't use languages we don't set segments:
		if len(languages) == 1 and languages[0] == '':
			return

		# Get the Full name of the language
		if language:
			from djangoplicity.newsletters.models import Language
			language = str(Language.objects.get(lang=language))

		# Get the interest group id from Mailchimp
		(id, mc_languages) = self._get_languages()
		if id == -1:
			# No languages defined in Mailchimp we return to prevent
			# an exception when testing the segment
			return

		# Build the segment's options
		# if we have a language we only send to subscribers of this language
		# else (i.e.: master list) we only send to subscribes of *none* of the languages
		segment_opts = {
			'match': 'all',
			'conditions': [{
				'field': 'interests-%d' % id,
				'op': 'all' if language else 'none',
				'value': language if language else ','.join(mc_languages),
			}]
		}

		# Test the segment
		r = self.ml.connection.campaigns.segment_test(list_id=self.ml.list_id, options=segment_opts)
		if isinstance(r, dict) and 'error' in r:
			raise Exception('Testing segment "%s" failed: "%s"' % (str(segment_opts), r['error']))

		if not self.ml.connection.campaigns.update(cid=campaign.campaign_id,
				name='segment_opts', value=segment_opts):
			raise Exception('Updating segment "%s" failed' % str(segment_opts))

	def _update_campaign( self, nl, campaign_id, lang ):
		"""
		Update an existing campaign in MailChimp.
		"""

		self._check_languages(nl)

		campaigns = self.ml.connection.campaigns.list( filters={ 'list_id': self.ml.list_id, 'campaign_id': campaign_id } )

		if lang:
			# Fetch the local version of the newsletter
			# for the given language
			local = nl.get_local_version(lang)
			if not local:
				raise Exception('Can\'t find Local newsletter for Newsletter %d for language "%s"' % (nl.id, lang))

			#  Add the mailer_context to the newsletter:
			local.render( self.get_mailer_context() )

			# Set the variables accordingly:
			subject = local.subject
			from_email = local.from_email if local.from_email else local.source.from_email
			from_name = local.from_name if local.from_name else local.source.from_name
			html = local.html
			text = local.text
		else:
			#  Add the mailer_context to the newsletter:
			nl.render( self.get_mailer_context() )

			subject = nl.subject
			from_email = nl.from_email
			from_name = nl.from_name
			html = nl.html
			text = nl.text

		# Total is the number of campaigns matching the query (should only ever
		# be 1 or 0 as we filter on campaign_id)
		if 'total' in campaigns and campaigns['total'] > 0:

			values = {
				'subject': self._chop(subject, 150),
				'from_email': from_email,
				'from_name': from_name,
				'title': self._chop(subject, 100),
			}

			result = self.ml.connection.campaigns.update(cid=campaign_id, name='options', value=values)
			if 'errors' in result and result['errors']:
				raise Exception("MailChimp could not update the campaign, error: %s'." % result['errors'])

			values = {
				'html': html,
				'text': text,
			}

			result = self.ml.connection.campaigns.update(cid=campaign_id, name='content', value=values)
			if 'errors' in result and result['errors']:
				raise Exception("MailChimp could not update the campaign, error: %s'." % result['errors'])

			return ( campaign_id, False )
		else:
			return ( self._create_campaign( nl, lang ), True )

	def _create_campaign( self, nl, lang ):
		"""
		Create a new campaign in MailChimp
		"""

		self._check_languages(nl)

		if lang:
			# Fetch the local version of the newsletter
			# for the given language
			local = nl.get_local_version(lang)
			if not local:
				raise Exception('Can\'t find Local newsletter for Newsletter %d for language "%s"' % (nl.id, lang))

			#  Add the mailer_context to the newsletter:
			local.render( self.get_mailer_context() )

			# Set the variables accordingly:
			subject = local.subject
			from_email = local.from_email if local.from_email else local.source.from_email
			from_name = local.from_name if local.from_name else local.source.from_name
			html = local.html
			text = local.text
		else:
			#  Add the mailer_context to the newsletter:
			nl.render( self.get_mailer_context() )

			subject = nl.subject
			from_email = nl.from_email
			from_name = nl.from_name
			html = nl.html
			text = nl.text

		val = self.ml.connection.campaigns.create(
			type='regular',
			options={
				'list_id': self.ml.list_id,
				'subject': self._chop( subject, 150 ),
				'from_email': from_email,
				'from_name': from_name,
				'tracking': { 'opens': True, 'html_clicks': True, 'text_clicks': False },
				'title': self._chop( subject, 100 ),
				'authenticate': True,
				'auto_footer': False,
				'inline_css': True,
				'fb_comments': True,
			},
			content={
				'html': html,
				'text': text,
			}
		)

		if 'error' in val:
			raise Exception("MailChimp could not create the campaign, error %d: '%s'." % (val['code'], val['error']))
		return val['id']

	def _upload_newsletter( self, newsletter ):
		"""
		Upload a newsletter (and localised version if any) into MailChimp, and
		record the MailChimp campaign id.
		"""
		from djangoplicity.newsletters.models import MailChimpCampaign

		self._check_languages(newsletter)

		# Get a list of languages for the newsletters, starting with an empty
		# string for the original version
		languages = ['', ]
		languages.extend(newsletter.type.languages.values_list('lang', flat=True))

		for language in languages:
			# Only upload ready translations
			if language:
				local = newsletter.get_local_version(language)
				if not local:
					raise Exception('Can\'t find Local newsletter for Newsletter %s for language "%s"' % (newsletter.id, language))

				if not local.translation_ready:
					continue

			( info, created ) = MailChimpCampaign.objects.get_or_create( newsletter=newsletter,
									list_id=self.ml.list_id, lang=language )

			if not created and info.campaign_id:
				( info.campaign_id, touched ) = self._update_campaign( newsletter, info.campaign_id, language )
				if touched:
					info.save()
			else:
				info.campaign_id = self._create_campaign( newsletter, language )
				info.save()

			# Set the Newsletter segments:
			self._set_segment(info, language, languages)

	def _get_languages( self ):
		"""
		Return the id of the 'Preferred language' group in Mailchimp as well as
		the list of preferred languages from the list
		"""
		id = -1
		mc_languages = []
		groups = self.ml.connection.lists.interest_groupings(id=self.ml.list_id)

		#  'groups' will be a list on success, or a dict on error:
		if isinstance(groups, dict) and 'error' in groups:
			# MailChimp returns an error if no groups are defined,
			# but we catch this later:
			if groups['error'] == 'This list does not have interest groups enabled':
				return (id, mc_languages)
			else:
				raise Exception(groups['error'])
		for group in groups:
			if group['name'].startswith('Preferred language'):
				id = group['id']
				for g in group['groups']:
					mc_languages.append(g['name'])

		return (id, mc_languages)

	def _check_languages( self, newsletter ):
		"""
		Check that the newsletter languages (if any) match the Mailchimp list's
		"""

		# Get a list of the newsletter's languages:
		nl_languages = newsletter.type.languages.all()

		# If the newsletter doesn't use languages we send to the
		# whole list so we can ignore the test
		if not nl_languages:
			return

		# Convert from code (e.g.: es-cl) to full name (e.g.: Spanish/Chile)
		nl_languages = [ str(lang) for lang in nl_languages ]

		# Get a list of the Mailchimp list's languages:
		mc_languages = self._get_languages()[1]

		# Check that languages are identical on both sides:
		for lang in nl_languages:
			if lang not in mc_languages:
				raise Exception("Language '%s' missing in MailChimp 'Preferred language' group for list '%s'"
						% (lang, self.ml.list_id))
		for lang in mc_languages:
			if lang not in nl_languages:
				raise Exception("Language '%s' missing in list's '%s' languages"
						% (lang, newsletter.type.name))

	def _get_campaigns(self, newsletter):
		"""
		Returns a list of (language, campaign) for each scheduled
		version of the newsletter (i.e.: original and translated)
		"""
		from djangoplicity.newsletters.models import MailChimpCampaign

		campaigns = []

		# Get a list of languages for the newsletters, starting with an empty
		# string for the original version
		languages = ['', ]
		languages.extend(newsletter.type.languages.values_list('lang', flat=True))

		for language in languages:
			# Check if the translation is ready:
			if language:
				local = newsletter.get_local_version(language)
				if not local:
					raise Exception('Can\'t find Local newsletter for Newsletter %d for language "%s"' % (newsletter.id, language))

				if not local.translation_ready:
					continue

			# Fetch the MailChimpCampaign for the given language
			try:
				campaign = MailChimpCampaign.objects.get(newsletter=newsletter,
								list_id=self.ml.list_id, lang=language)
			except MailChimpCampaign.DoesNotExist:
				raise Exception('Could not find MailChimpCampaign for list "%d" with language "%s"' % (newsletter.id, language))

			campaigns.append((language, campaign))

		return campaigns

	def get_mailer_context(self):
		return {
			'unsubscribe_link': '*|UNSUB|*',  # MailChimp will automatically replace the tag *|...|*-tags with a lists unsubscribe link etc.
			'preferences_link': '*|UPDATE_PROFILE|*',
			'browser_link': '*|ARCHIVE|*' if self.enable_browser_link else '',
			'is_mailchimp_mailer': True,
		}

	def on_scheduled( self, newsletter ):
		"""
		Notification that a newsletter was scheduled for sending.
		"""
		self._upload_newsletter( newsletter )

	def send_now( self, newsletter ):
		"""
		Send newsletter now.
		"""
		self._check_languages(newsletter)

		self._upload_newsletter( newsletter )

		campaigns = self._get_campaigns(newsletter)

		languages = ['', ]
		languages.extend(newsletter.type.languages.values_list('lang', flat=True))

		# Update the segments based on languages (if any)
		for language, campaign in campaigns:
			self._set_segment(campaign, language, languages)

		# We loop a second time to make sure all segments are updated
		# correctly before trying to actually send the newsletter
		for language, campaign in campaigns:
			r = self.ml.connection.campaigns.send( cid=campaign.campaign_id )
			# Test for errors
			try:
				if 'error' in r:
					return 'MailChimp could not send newsletter: "%s"' % r['error']
			except TypeError:
				if not r:
					return 'MailChimp could not send newsletter.'

	def send_test( self, newsletter, emails ):
		"""
		Send a test email for this newsletter
		"""
		self._upload_newsletter( newsletter )

		campaigns = self._get_campaigns(newsletter)

		for language, campaign in campaigns:
			r = self.ml.connection.campaigns.send_test( cid=campaign.campaign_id, test_emails=emails )
			# Test for errors
			try:
				if 'error' in r:
					return 'MailChimp could not send test email: "%s"' % r['error']
			except TypeError:
				if not r:
					return 'MailChimp could not send test email.'
