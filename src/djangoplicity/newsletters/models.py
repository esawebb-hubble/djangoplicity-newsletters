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

"""

from datetime import datetime, timedelta
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import Signal, receiver
from djangoplicity.newsletters.exceptions import MailChimpError
from mailsnake import MailSnake
from djangoplicity.newsletters.mailman import MailmanList
from urllib2 import HTTPError, URLError
import hashlib
import uuid as uuidmod

# Work around fix - see http://stackoverflow.com/questions/1210458/how-can-i-generate-a-unique-id-in-python
uuidmod._uuid_generate_time = None
uuidmod._uuid_generate_random = None

#
# Settings
#
NEWSLETTERS_MAILCHIMP_APIKEY = settings.NEWSLETTERS_MAILCHIMP_APIKEY if hasattr( settings, 'NEWSLETTERS_MAILCHIMP_APIKEY' ) else ''
LIST_URL = 'http://www.eso.org/lists'

#
# Signals
#
subscription_added = Signal( providing_args=["subscription", "source" ] )
subscription_deleted = Signal( providing_args=["list", "subscriber", "source" ] )

#
# Models
#
class BadEmailAddress( models.Model ):
	"""
	Bad email addresses which was found to bounce back emails.  
	"""
	email = models.EmailField( unique=True )
	timestamp = models.DateTimeField( auto_now_add=True )

	def __unicode__( self ):
		return self.email

	class Meta:
		ordering = ( 'email', )
		verbose_name_plural = "bad email addresses"


class Subscriber( models.Model ):
	"""
	Subscriber (i.e an email address) to one or more lists.  
	"""
	email = models.EmailField( unique=True )

	def __unicode__( self ):
		return self.email

	class Meta:
		ordering = ( 'email', )

class List( models.Model ):
	"""
	List name of subscribers.
	
	Sync'ed with mailman.
	"""
	name = models.SlugField( unique=True )
	password = models.SlugField()
	subscribers = models.ManyToManyField( Subscriber, through='Subscription', blank=True )

	def _get_mailman( self ):
		"""
		Get object for manipulating mailman list.
		"""
		return MailmanList( name=self.name, password=self.password, main_url="http://www.eso.org/lists" )
	mailman = property( _get_mailman )


	def subscribe( self, subscriber, source=None ):
		"""
		Subscribe a user to this list. 
		"""
		sub = Subscription( list=self, subscriber=subscriber )
		sub.save()

		# Send signal to allow mailman and mailchimp to be updated
		subscription_added.send_robust( sender=self, subscription=sub, source=source )


	def unsubscribe( self, subscriber, source=None ):
		"""
		Unsubscribe a user to this list. 
		"""
		try:
			sub = Subscription.objects.get( list=self, subscriber=subscriber )
			sub.delete()

			# Send signal to allow mailman and mailchimp to be updated
			subscription_deleted.send_robust( sender=self, list=self, subscriber=subscriber, source=source )
		except Subscription.DoesNotExist:
			pass


	def incoming_changes( self ):
		"""
		Get differences between mailman and djangoplicity list.
		"""
		mailman_members = self.mailman.get_members()

		if mailman_members:
			mailman_names, mailman_emails = zip( *mailman_members )
			mailman_emails = set( mailman_emails )
		else:
			mailman_names, mailman_emails = [], set( [] )

		current_list_subscribers = self.subscribers.all()
		current_emails = set( [s.email for s in current_list_subscribers] )

		bad_emails = set( [x.email for x in BadEmailAddress.objects.all()] )
		mailman_unsubscribe_emails = mailman_emails & bad_emails # Remove all mailman emails that has been detected as bad emails.

		subscribe_emails = (mailman_emails - current_emails) - mailman_unsubscribe_emails
		unsubscribe_emails = ( current_emails - mailman_emails ) | ( current_emails & mailman_unsubscribe_emails )

		return ( subscribe_emails, unsubscribe_emails, current_list_subscribers, mailman_unsubscribe_emails )


	@classmethod
	def subscription_added_handler( cls, sender=None, subscription=None, source=None, **kwargs ):
		"""
		Handler for dealing with new subscriptions.
		"""
		if not isinstance( source, cls ):
			# Event was not sent from new mailman subscription, so 
			# it must be passed on to mailman
			from djangoplicity.newsletters.tasks import mailman_send_subscribe
			mailman_send_subscribe.delay( subscription.list.name, subscription.subscriber.email )


	@classmethod
	def subscription_deleted_handler( cls, sender, list=None, subscriber=None, source=None, **kwargs ):
		"""
		Handler for dealing with unsubscribes. 
		"""
		if not isinstance( source, cls ):
			# Event was not sent from new mailman subscription, so 
			# it must be passed on to mailman
			from djangoplicity.newsletters.tasks import mailman_send_unsubscribe
			mailman_send_unsubscribe.delay( list.name, subscriber.email )

	@classmethod
	def post_save_handler( cls, sender=None, instance=None, created=False, raw=False, **kwargs ):
		"""
		Start task to setup get subscribers from mailman
		"""
		from djangoplicity.newsletters.tasks import synchronize_mailman

		if created and not raw:
			synchronize_mailman.delay( list_name=instance.name )

	def __unicode__( self ):
		return self.name

	class Meta:
		ordering = ( 'name', )


# Connect signal handlers
subscription_added.connect( List.subscription_added_handler )
subscription_deleted.connect( List.subscription_deleted_handler )
post_save.connect( List.post_save_handler, sender=List )


class Subscription( models.Model ):
	"""
	Relation between subscribers and lists.
	"""
	subscriber = models.ForeignKey( Subscriber )
	list = models.ForeignKey( List )

	def __unicode__( self ):
		return "%s subscribed to %s" % ( self.subscriber, self.list )

	class Meta:
		unique_together = ( 'subscriber', 'list' )
		ordering = ( 'subscriber__email', )


class MailChimpList( models.Model ):
	"""
	A list already defined in MailChimp.
	
	Most information will be fetched directly from MailChimp.
	
	Note, the mailchimp API does not support list creation, 
	so each list must manually be created via the MailChimp API.
	"""
	# Model properties defined in djangoplicity
	api_key = models.CharField( max_length=255, default=NEWSLETTERS_MAILCHIMP_APIKEY, verbose_name="API key" )
	list_id = models.CharField( unique=True, max_length=50 )

	synchronize = models.BooleanField( default=False )
	sources = models.ManyToManyField( List, through='MailChimpSourceList' )
	subscriber_excludes = models.ManyToManyField( Subscriber, through='MailChimpSubscriberExclude' )

	# Model properties replicated from MailChimp
	name = models.CharField( max_length=255, blank=True )
	web_id = models.CharField( blank=True, max_length=255 )
	email_type_option = models.CharField( max_length=50, blank=True )
	use_awesomebar = models.BooleanField( default=False )
	default_from_name = models.CharField( max_length=255, blank=True )
	default_from_email = models.CharField( max_length=255, blank=True )
	default_subject = models.CharField( max_length=255, blank=True )
	default_language = models.CharField( max_length=10, blank=True )
	list_rating = models.IntegerField( blank=True, null=True )
	member_count = models.IntegerField( blank=True, null=True )
	unsubscribe_count = models.IntegerField( blank=True, null=True )
	cleaned_count = models.IntegerField( blank=True, null=True )
	member_count_since_send = models.IntegerField( blank=True, null=True )
	unsubscribe_count_since_send = models.IntegerField( blank=True, null=True )
	cleaned_count_since_send = models.IntegerField( blank=True, null=True )
	avg_sub_rate = models.IntegerField( blank=True, null=True, help_text="per month" )
	avg_unsub_rate = models.IntegerField( blank=True, null=True, help_text="per month" )
	target_sub_rate = models.IntegerField( blank=True, null=True, help_text="per month" )
	open_rate = models.IntegerField( blank=True, null=True, help_text="per campaign" )
	click_rate = models.IntegerField( blank=True, null=True, help_text="per campaign" )

	# Status properties
	connected = models.BooleanField( default=False )
	last_sync = models.DateTimeField( blank=True, null=True )

	def mailchimp_dc( self ):
		"""
		Get the MailChimp data center for an instance's API key.
		"""
		if self.api_key:
			dc = 'us1'
			if '-' in self.api_key:
				dc = self.api_key.split( '-' )[1]
			return dc
		return None

	def get_admin_url( self ):
		"""
		Get URL to MailChimp's admin interface for list. 
		"""
		dc = self.mailchimp_dc()
		if dc and self.web_id:
			return "https://%s.admin.mailchimp.com/lists/dashboard/overview?id=%s" % ( dc, self.web_id )
		else:
			return None

	def _get_connection( self ):
		"""
		Return a mailsnake object that can be used to interact with 
		the MailChimp API.
		"""
		return MailSnake( self.api_key )
	connection = property( _get_connection )

	def default_lists( self ):
		"""
		Get the default lists associated with this mailchimp list. 
		"""
		return self.sources.filter( mailchimpsourcelist__default=True )

	def save( self, *args, **kwargs ):
		"""
		Save instance (and sync info from MailChimp if it hasn't been done before).
		"""
		if self.list_id and self.api_key and not self.web_id:
			try:
				self.fetch_info()
			except MailChimpError, e:
				self.connected = False
				self.last_sync = datetime.now()
				self.error = unicode( e )
		super( MailChimpList, self ).save( *args, **kwargs )

	def get_subscribers( self ):
		""" Get source lists subscribers  """
		return Subscriber.objects.exclude( pk__in=self.subscriber_excludes.all() ).filter( subscription__list__in=self.sources.all() ).distinct()

	def get_subscriptions( self ):
		""" Get source list subscriptions """
		return Subscription.objects.filter( list__in=self.sources.all() ).exclude( subscriber__in=self.subscriber_excludes.all() )

	def fetch_info( self ):
		"""
		Synchronize information from MailChimp list to Djangoplicity
		
		mailsnake.lists - see http://apidocs.mailchimp.com/1.3/lists.func.php
		"""
		try:
			res = self.connection.lists( filters={ 'list_id' : self.list_id } )
			if res['total'] == 1:
				info = res['data'][0]

				self.name = info.get( 'name', '' )
				self.web_id = info.get( 'web_id', '' )
				self.email_type_option = info.get( 'email_type_option', '' )
				self.use_awesomebar = info.get( 'use_awesomebar', False )
				self.default_from_name = info.get( 'default_from_name', '' )
				self.default_from_email = info.get( 'default_from_email', '' )
				self.default_subject = info.get( 'default_subject', '' )
				self.default_language = info.get( 'default_language', '' )
				self.list_rating = info.get( 'list_rating', None )
				self.member_count = info['stats'].get( 'member_count', None )
				self.unsubscribe_count = info['stats'].get( 'unsubscribe_count', None )
				self.cleaned_count = info['stats'].get( 'cleaned_count', None )
				self.member_count_since_send = info['stats'].get( 'member_count_since_send', None )
				self.unsubscribe_count_since_send = info['stats'].get( 'unsubscribe_count_since_send', None )
				self.cleaned_count_since_send = info['stats'].get( 'cleaned_count_since_send', None )
				self.avg_sub_rate = info['stats'].get( 'avg_sub_rate', None )
				self.avg_unsub_rate = info['stats'].get( 'avg_unsub_rate', None )
				self.target_sub_rate = info['stats'].get( 'target_sub_rate', None )
				self.open_rate = info['stats'].get( 'open_rate', None )
				self.click_rate = info['stats'].get( 'click_rate', None )

				self.last_sync = datetime.now()
				self.connected = True
				self.error = ""
			else:
				raise Exception( "Unknown MailChimp error." )
		except ( HTTPError, URLError ), e:
			raise MailChimpError( http_error=e )
		except KeyError, e:
			raise MailChimpError( response=res )


	def _list_all_members( self, status ):
		"""
		Helper function to paginate through all members 
		"""
		grand_total = 0
		data = []

		total = self.member_count
		limit = 1000
		start = 0

		while total > 0:
			try:
				res = self.connection.listMembers( id=self.list_id, status=status, start=start, limit=1000 )
				grand_total += res['total']
				data += res['data']

				total -= limit
				start += 1
			except ( HTTPError, URLError ), e:
				raise MailChimpError( http_error=e )
			except KeyError, e:
				raise MailChimpError( response=res )

		return { 'total' : grand_total, 'data' : data }


	def outgoing_changes( self ):
		"""
		"""
		self.fetch_info()
		res = self._list_all_members( 'subscribed' )

		mailchimp_subscribers = set( [x['email'] for x in res['data']] )
		current_subscribers = set( [x.email for x in self.get_subscribers()] )

		subscribe_emails = current_subscribers - mailchimp_subscribers
		unsubscribe_emails = mailchimp_subscribers - current_subscribers

		return ( subscribe_emails, unsubscribe_emails )


	@classmethod
	def subscription_added_handler( cls, sender=None, subscription=None, source=None, **kwargs ):
		"""
		Handler for dealing with new subscriptions.
		"""
		if not isinstance( source, cls ):
			# Event was not sent from new MailChimp subscription, so 
			# it must be passed on to MailChimp
			from djangoplicity.newsletters.tasks import mailchimp_send_subscribe
			mailchimp_send_subscribe.delay( subscription.list.name, subscription.subscriber )

	@classmethod
	def subscription_deleted_handler( cls, sender=None, list=None, subscriber=None, source=None, **kwargs ):
		"""
		Handler for dealing with unsubscribes. 
		"""
		if not isinstance( source, cls ):
			# Event was not sent from new MailChimp subscription, so 
			# it must be passed on to MailChimp
			from djangoplicity.newsletters.tasks import mailchimp_send_unsubscribe
			mailchimp_send_unsubscribe.delay( list.name, subscriber )

	@classmethod
	def post_save_handler( cls, sender=None, instance=None, created=False, raw=False, **kwargs ):
		"""
		Start task to setup list in MailChimp (e.g. add webhooks).
		"""
		from djangoplicity.newsletters.tasks import webhooks

		if created and not raw:
			webhooks.delay( list_id=instance.list_id )

	@classmethod
	def pre_delete_handler( cls, sender=None, instance=None, **kwargs ):
		"""
		Start task to cleanup list in MailChimp (e.g. remove webhooks).
		"""
		from djangoplicity.newsletters.tasks import mailchimp_cleanup
		mailchimp_cleanup.delay( api_key=instance.api_key, list_id=instance.list_id )

	def __unicode__( self ):
		return self.name if self.name else self.list_id

	class Meta:
		ordering = ( 'name', )


# Connect signal handlers
subscription_added.connect( MailChimpList.subscription_added_handler )
subscription_deleted.connect( MailChimpList.subscription_deleted_handler )
post_save.connect( MailChimpList.post_save_handler, sender=MailChimpList )
pre_delete.connect( MailChimpList.pre_delete_handler, sender=MailChimpList )


class MailChimpSubscriberExclude( models.Model ):
	"""
	Model to track subscribers which should be exclude from certain 
	MailChimp lists (usually due to unsubscribing from the newsletter).
	"""
	mailchimplist = models.ForeignKey( MailChimpList )
	subscriber = models.ForeignKey( Subscriber )

	class Meta:
		unique_together = ( 'mailchimplist', 'subscriber' )


class MailChimpSourceList( models.Model ):
	"""
	Source lists for mailchimp lists (i.e which lists
	the MailChimp lists should be generated from).
	
	The default list will receive all subscriptions made
	in MailChimp. 
	"""
	mailchimplist = models.ForeignKey( MailChimpList )
	list = models.ForeignKey( List )
	default = models.BooleanField( default=False )

	@classmethod
	def post_save_handler( cls, sender=None, instance=None, created=False, raw=False, **kwargs ):
		"""
		A relation was created between mailman and mailchimp list 
		"""
		#print "MailChimpSourceList.post_save_handler"
		if created and not raw:
			from djangoplicity.newsletters.tasks import synchronize_mailchimplist
			synchronize_mailchimplist( instance.mailchimplist.list_id )


	@classmethod
	def post_delete_handler( cls, sender=None, instance=None, **kwargs ):
		"""
		A relation between mailman and mailchimp list was removed. 
		"""
		from djangoplicity.newsletters.tasks import synchronize_mailchimplist
		synchronize_mailchimplist( instance.mailchimplist.list_id )
		# TODO: call .delay instead


	class Meta:
		unique_together = ( 'mailchimplist', 'list' )

# Connect signal handlers
post_save.connect( MailChimpSourceList.post_save_handler, sender=MailChimpSourceList )
post_delete.connect( MailChimpSourceList.post_delete_handler, sender=MailChimpSourceList )

class MailChimpListToken( models.Model ):
	"""
	Tokens used in get parameters to secure webhook requests 
	from MailChimp.
	"""
	list = models.ForeignKey( MailChimpList )
	uuid = models.CharField( unique=True, max_length=36, verbose_name="UUID" )
	token = models.CharField( unique=True, max_length=56 )
	expired = models.DateTimeField( null=True, blank=True )

	@classmethod
	def create( cls, list ):
		"""
		Create a MailChimpListToken for a MailChimpList.
		"""
		if not list.list_id:
			raise Exception( "List is empty, cannot create token" )

		uuid = str( uuidmod.uuid4() )
		token = cls.token_value( list.list_id, uuid )

		obj = cls( list=list, uuid=uuid, token=token )
		obj.save()

		return obj

	@staticmethod
	def token_value( list_id, uuid ):
		"""
		Generate token value from list_id and uuid
		"""
		m = hashlib.sha224()
		m.update( settings.SECRET_KEY )
		m.update( list_id )
		m.update( uuid )
		return str( m.hexdigest() )

	@classmethod
	def get_token( cls, token ):
		try:
			return cls.objects.filter( token=token ).filter( models.Q( expired__lte=datetime.now() - timedelta( minutes=10 ) ) | models.Q( expired__isnull=True ) ).get()
		except cls.DoesNotExist:
			return None

	def validate_token( self, list ):
		"""
		Validate input parameters
		"""
		if list and self.list.pk == list.pk:
			return True
		else:
			return False 

	def hook_params( self ):
		"""
		Return a dict of query parameters for a MailChimp webhook 
		"""
		return { 'token' : self.token, 'uuid' : self.uuid }
