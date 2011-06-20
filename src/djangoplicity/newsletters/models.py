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
from djangoplicity.newsletters.exceptions import MailChimpError
from mailsnake import MailSnake
from urllib2 import HTTPError, URLError
import uuid as uuidmod
import hashlib

# Work around fix - see http://stackoverflow.com/questions/1210458/how-can-i-generate-a-unique-id-in-python
uuidmod._uuid_generate_time = None
uuidmod._uuid_generate_random = None


#
# Settings
#
NEWSLETTERS_MAILCHIMP_APIKEY = settings.NEWSLETTERS_MAILCHIMP_APIKEY if hasattr( settings, 'NEWSLETTERS_MAILCHIMP_APIKEY' ) else ''
LIST_URL = 'http://www.eso.org/lists'

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
	source_lists = models.ManyToManyField( 'self', through='ListSynchronization', blank=True, symmetrical=False )

	def __unicode__( self ):
		return self.name

	class Meta:
		ordering = ( 'name', )

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
		
class ListSynchronization( models.Model ):
	"""
	"""
	destination = models.ForeignKey( List )
	source = models.ForeignKey( List, related_name='+' )
	
	def __unicode__(self):
		return "Synchronize subscribers from %s to %s" % ( self.source, self.destination )
	
	# TODO: Add validation of objects (e.g. no self sync, cyclic definitions).

ACTION_CHOICES = (
	('sub','Subscribe'),
	('unsub','Subscribe'),
)

class ListActionLog( models.Model ):
	list = models.ForeignKey( List )
	subscriber = models.ForeignKey( Subscriber )
	action = models.CharField( max_length=5, choices=ACTION_CHOICES, db_index=True )
	timestamp = models.DateTimeField( autonow_add=True )


class MailChimpList( models.Model ):
	"""
	Li
	"""
	# Model properties defined in djangoplicity
	api_key = models.CharField( max_length=255, default=NEWSLETTERS_MAILCHIMP_APIKEY, verbose_name="API key" )
	list_id = models.CharField( unique=True, max_length=50 )
	#sources = models.ManyToManyField( List, through='MailChimpListSource', blank=True )

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
	
	def save(self, *args, **kwargs ):
		"""
		Save instance (and sync info from MailChimp if it hasn't been done before).
		"""
		if self.list_id and self.api_key and not self.web_id:
			try:
				self.sync_info()
			except MailChimpError, e:
				self.connected = False
				self.last_sync = datetime.now()
				self.error = unicode( e )
		super( MailChimpList, self ).save( *args, **kwargs )
		
	def get_source_subscribers( self ):
		""" Get source lists subscribers  """
		return Subscriber.objects.filter( subscription__list__in=self.sources.all() ).distinct()
	
	def get_source_subscriptions(self):
		""" Get source lists subscriptions """
		return Subscription.objects.filter( list__in=self.sources.all() )

	def sync_info( self ):
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

	def __unicode__( self ):
		return self.name if self.name else self.list_id

	class Meta:
		ordering = ( 'name', )
	

class MailChimpListToken( models.Model ):
	"""
	Tokens used to secure webhook requests from MailChimp
	"""
	list = models.ForeignKey( MailChimpList )
	uuid = models.CharField( unique=True, max_length=36 )
	token = models.CharField( unique=True, max_length=56 )
	expired = models.DateTimeField( null=True, blank=True )
	
	@classmethod
	def create( cls, list ):
		"""
		Create a MailChimpListToken for a MailChimpList.
		"""
		if not list.list_id:
			raise Exception("List is empty, cannot create token")
		
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
	def validate_token( cls, list_id, uuid, token ):
		"""
		Validate input parameters
		"""
		expected_token = cls.token_value( list_id, uuid )
		if token == expected_token:
			# Token is valid, so let's hit the db and check if it's expired
			# A token is valid 15 minutes after it expired, to allow for MailChimp to update it's
			# data.
			return cls.objects.filter( token=token ).filter( models.Q( expired__lte=datetime.now() - timedelta( minutes=10 ) ) | models.Q( expired__isnull=True ) ).exists()	
		return False

	def hook_params( self ):
		"""
		Return a dict of query parameters for a MailChimp webhook 
		"""
		return { 'token' : self.token, 'uuid' : self.uuid }
		

class MailChimpListSource( models.Model ):
	mailchimplist = models.ForeignKey( MailChimpList, verbose_name='mail chimp list' )
	list = models.ForeignKey( List )
	
	class Meta:
		ordering = ( 'list__name', 'mailchimplist__name', )