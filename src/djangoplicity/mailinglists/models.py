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
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.db import models
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import Signal, receiver
from django.utils.encoding import smart_unicode
from djangoplicity.actions.models import Action, EventAction
from djangoplicity.mailinglists.exceptions import MailChimpError
from djangoplicity.mailinglists.mailman import MailmanList
from mailsnake import MailSnake
from urllib import urlencode, quote
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

def _object_identifier( obj ):
	"""
	Return an objects identifier for a model object (e.g. contacts.contact:2579)
	"""
	if isinstance( obj, models.Model ):
		return "%s:%s" % ( smart_unicode( obj._meta ), smart_unicode( obj.pk, strings_only=True ) )
	else:
		return ""

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
	Mailman list
	"""
	base_url = models.CharField( max_length=255 )
	name = models.SlugField( unique=True )
	password = models.SlugField()
	subscribers = models.ManyToManyField( Subscriber, through='Subscription', blank=True )
	last_sync = models.DateTimeField( blank=True, null=True )

	def _get_mailman( self ):
		"""
		Get object for manipulating mailman list.
		"""
		return MailmanList( name=self.name, password=self.password, main_url=self.base_url )
	mailman = property( _get_mailman )

	def subscribe( self, subscriber=None, email=None, async=True ):
		"""
		Subscribe a user to this list. 
		"""
		if not subscriber:
			if email:
				try:
					BadEmailAddress.objects.get( email=email )
					raise Exception( "%s is a known bad email address" % email )
				except BadEmailAddress.DoesNotExist:
					pass

				( subscriber, created ) = Subscriber.objects.get_or_create( email=email )
			else:
				raise Exception( "Please provide either subscriber or email address" )

		sub = Subscription( list=self, subscriber=subscriber )
		sub.save()

		if async:
			from djangoplicity.mailinglists.tasks import mailman_send_subscribe
			mailman_send_subscribe.delay( sub.pk )
		else:
			self._subscribe( subscriber.email )

	def unsubscribe( self, subscriber=None, email=None, async=True ):
		"""
		Unsubscribe a user to this list. 
		"""
		try:
			if subscriber:
				sub = Subscription.objects.get( list=self, subscriber=subscriber )
			elif email:
				sub = Subscription.objects.get( list=self, subscriber__email=email )
			else:
				raise Exception( "Expected either subscriber or email keyword arguments to be provided." )

			if async:
				from djangoplicity.mailinglists.tasks import mailman_send_unsubscribe
				mailman_send_unsubscribe.delay( sub.pk )
			else:
				email = sub.subscriber.email
				sub.delete()
				self._unsubscribe( email )
		except Subscription.DoesNotExist, e:
			raise e

	def _subscribe( self, email ):
		"""
		Method that will directly subscribe an email to this list (normally called from
		a background task.) 
		"""
		self.mailman.subscribe( email )

	def _unsubscribe( self, email ):
		"""
		Method that will directly unsubscribe an email to this list (normally called from
		a background task.
		"""
		self.mailman.unsubscribe( email )

	def get_mailman_emails( self ):
		"""
		Get all current mailman subscribers.
		"""
		mailman_members = self.mailman.get_members()

		if mailman_members:
			mailman_names, mailman_emails = zip( *mailman_members )
			mailman_emails = set( mailman_emails )
		else:
			mailman_names, mailman_emails = [], set( [] )

		return mailman_emails

	def update_subscribers( self, emails ):
		"""
		Update the list of subscribers to match a list of emails.
		"""
		emails = dict( [( x, 1 ) for x in emails] ) # Remove duplicates

		for sub in Subscription.objects.filter( list=self ).select_related( depth=1 ):
			if sub.subscriber.email in emails:
				del emails[sub.subscriber.email]
			else:
				# Delete all subscribers not in the list
				sub.delete()

		bad_emails = set( BadEmailAddress.objects.all().values_list( 'email', flat=True ) )
		emails = set( emails.keys() )

		# Subscribe all emails not in subscribers.
		for email in ( emails - bad_emails ):
			( subscriber, created ) = Subscriber.objects.get_or_create( email=email )
			sub = Subscription( list=self, subscriber=subscriber )
			sub.save()


	def push( self, remove_existing=True ):
		"""
		Push entire list of subscribers to mailman (will overwrite anything in Mailman)
		"""
		mailman_emails = self.get_mailman_emails()
		django_emails = set( self.subscribers.all().values_list( 'email', flat=True ) )

		subscribe = django_emails - mailman_emails
		unsubscribe = mailman_emails - django_emails

		for e in subscribe:
			self._subscribe( e )

		if remove_existing:
			for e in unsubscribe:
				self._unsubscribe( e )

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
	""" Enable list to be sync'ed with mailchimp. """

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
	""" Designates if the list is being successfully sync'ed with MailChimp. """

	last_sync = models.DateTimeField( blank=True, null=True )
	""" Designates last time a sync was done for this list. """

	# Model link
	content_type = models.ForeignKey( ContentType, null=True, blank=True, help_text="Select the content type of objects that subscribers on this list can be linked with." )
	primary_key_field = models.ForeignKey( 'MailChimpMergeVar', blank=True, null=True )

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


	def get_merge_vars( self ):
		"""
		Get all defined MERGE VARS for this list.
		"""
		return MailChimpMergeVar.objects.filter( list=self ).order_by( 'order' )

	def parse_merge_vars( self, params ):
		"""
		Given MERGE VAR parameters, map it to field values.
		"""
		mapping = {}

		if self.primary_key_field and self.content_type:
			for m in MergeVarMapping.objects.filter( list=self ).select_related():
				mapping.update( dict( m.parse_merge_var( params ) ) )
		return mapping

	def create_merge_vars( self, obj, changes=None ):
		"""
		Create a MERGE VARS dictionary from a model object. The model object
		must have the same content type as defined in content_type field. Hence
		both content_type and primiary_key_field must be specified for the list.
		
		The mapping from model object field to MERGE VAR is defined by MergeVarMapping model.
		
		If the MERGE VAR dictionary should only contain updates, you need to pass a ``changes''
		dictionary with model field names as keys and 2-tuples as values. The 2-tuples should contain
		the before and after value::
		
			changes = {
				'email' : ( 'email+old@eso.org', 'email+new@eso.org' ),
				# ...
			}
			
		The changes dictionary can easily be created with django-dirtyfields app. 
		See http://pypi.python.org/pypi/django-dirtyfields 
		"""
		merge_vars = {}
		if self.content_type and self.primary_key_field and isinstance( obj, self.content_type.model_class() ):
			if changes is None:
				merge_vars[self.primary_key_field.tag] = "%s:%s" % ( smart_unicode( obj._meta ), smart_unicode( obj.pk, strings_only=True ) )

			for m in MergeVarMapping.objects.filter( list=self ).select_related():
				( tag, val ) = m.create_merge_var( obj, changes=changes )
				if val and tag != self.primary_key_field.tag:
					merge_vars[tag] = val

		return merge_vars

	def get_modelpk_from_identifier( self, object_identifier ):
		"""
		"""
		model_identifier, pk = object_identifier.split( ":" )
		app_label, model_name = model_identifier.split( "." )

		if app_label == self.content_type.app_label and model_name == self.content_type.model:
			return ( app_label, model_name, pk )
		return None

	def get_object_from_identifier( self, object_identifier ):
		"""
		"""
		val = self.get_modelpk_from_identifier( object_identifier )
		if val:
			app_label, model_name, pk = val
			Model = models.get_model( app_label, model_name )
			return Model.objects.get( pk=pk )
		return None


	def get_object_from_mergevars( self, params ):
		"""
		If list is linked with a django model (i.e content_type and primary_key_field is set), then this method
		will retrieve the model object 
		"""
		# get object_identifier from params, and extract dictionary mapping
		if self.primary_key_field and self.content_type:
			pk_tag = self.primary_key_field.tag

			if pk_tag in params and params[pk_tag]:
				# Ensure pk_tag is in merge vars and it's non-empty.
				return self.get_object_from_identifier( params[pk_tag] )
		return None

	def get_object_from_exportvars( self, data ):
		"""
		If list is linked with a django model (i.e content_type and primary_key_field is set), then this method
		will retrieve the model object 
		"""
		# get object_identifier from params, and extract dictionary mapping
		if self.primary_key_field and self.content_type:
			pk_name = self.primary_key_field.name

			if pk_name in data and data[pk_name]:
				# Ensure pk_tag is in merge vars and it's non-empty.
				return self.get_object_from_identifier( data[pk_name] )
		return None

	def subscribe( self, email, merge_vars={}, email_type='html', double_optin=True, send_welcome=False, async=True ):
		"""
		Subscribe the provided email address. If user is already subscribed an error will be returned. 

		Mailchimp descriptions of flags:
		
		  * email_type - email type preference for the email ( html, text, or mobile defaults to html )
		  * double_optin - flag to control whether a double opt-in confirmation message is sent, defaults to true. Abusing this may cause your account to be suspended.
		  * send_welcome -  if your double_optin is false and this is true, we will send your lists Welcome Email if this subscribe succeeds - this will *not* fire if we end up updating an existing subscriber. If double_optin is true, this has no effect. defaults to false.
		"""
		# validate email address
		validate_email( email )

		try:
			BadEmailAddress.objects.get( email=email )
			raise Exception( "%s is a known bad email address" % email )
		except BadEmailAddress.DoesNotExist:
			pass

		# validate email_type
		if email_type not in ['html', 'text', 'mobile']:
			raise Exception( "Invalid email type %s - options are html, text, or mobile." % email_type )

		# Check merge vars.
		allowed_vars = self.get_merge_vars().values_list( 'tag', flat=True )

		for k, v in merge_vars.items():
			if k not in allowed_vars:
				raise Exception( "Invalid merge var %s - allowed variables are %s" % ( k, ", ".join( allowed_vars ) ) )

		# Send subscribe
		res = self.connection.listSubscribe( 
			id=self.list_id,
			email_address=email,
			email_type=email_type,
			double_optin=double_optin,
			update_existing=False,
			replace_interests=False,
			send_welcome=send_welcome,
			merge_vars=merge_vars,
		)

		if res != True:
			raise MailChimpError( response=res )
		return True

	def unsubscribe( self, email, delete_member=False, send_goodbye=True, send_notify=True, async=True ):
		"""
		Unsubscribe email from MailChimp 
		
		Mailchimp descriptions of flags:
		
		  * email_address	the email address to unsubscribe OR the email "id" returned from listMemberInfo, Webhooks, and Campaigns
		  * delete_member	flag to completely delete the member from your list instead of just unsubscribing, default to false
		  * send_goodbye	flag to send the goodbye email to the email address, defaults to true
		  * send_notify	flag to send the unsubscribe notification email to the address defined in the list email notification settings, defaults to true
		"""
		# validate email address
		validate_email( email )

		# Send subscribe
		res = self.connection.listUnsubscribe( 
			id=self.list_id,
			email_address=email,
			delete_member=delete_member,
			send_goodbye=send_goodbye,
			send_notify=send_notify,
		)

		if res != True:
			raise MailChimpError( response=res )
		return True

	def update_profile( self, email, new_email, merge_vars={}, email_type=None, replace_interests=True, async=True ):
		"""
		Update the profile of an existing member
		"""
		# validate email address
		validate_email( email )
		validate_email( new_email )

		try:
			BadEmailAddress.objects.get( email=new_email )
			raise Exception( "%s is a known bad email address" % new_email )
		except BadEmailAddress.DoesNotExist:
			pass

		# validate email_type
		if email_type not in ['html', 'text', 'mobile', None]:
			raise Exception( "Invalid email type %s - options are html, text, mobile or <blank>." % email_type )

		# Check merge vars.
		allowed_vars = list( self.get_merge_vars().values_list( 'tag', flat=True ) ) + ['EMAIL', 'NEW_EMAIL', 'OPTIN_IP', 'OPTIN_TIME', 'MC_LOCATION']

		for k, v in merge_vars.items():
			if k not in allowed_vars:
				raise Exception( "Invalid merge var %s - allowed variables are %s" % ( k, ", ".join( allowed_vars ) ) )

		# Set the new email address
		merge_vars['EMAIL'] = new_email
		if 'NEW_EMAIL' in merge_vars:
			del merge_vars['NEW_EMAIL']

		# Send subscribe
		res = self.connection.listUpdateMember( 
			id=self.list_id,
			email_address=email,
			email_type=email_type,
			replace_interests=replace_interests,
			merge_vars=merge_vars,
		)

		if res != True:
			raise MailChimpError( response=res )
		return True

	def save( self, *args, **kwargs ):
		"""
		Save instance (and sync info from MailChimp if it hasn't been done before).
		"""
		super( MailChimpList, self ).save( *args, **kwargs )
		if self.list_id and self.api_key and not self.web_id:
			try:
				self.fetch_info()
			except MailChimpError, e:
				self.connected = False
				self.last_sync = datetime.now()
				self.error = unicode( e )
				self.save()

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

				# Try to get Merge Vars
				pks = []
				for v in self.connection.listMergeVars( id=self.list_id ):
					( obj, created ) = MailChimpMergeVar.objects.get_or_create( 
						list=self,
						name=v['name'],
						required=v['req'],
						field_type=v['field_type'],
						public=v['public'],
						show=v['show'],
						order=v['order'],
						default=v['default'] or '',
						size=v['size'],
						tag=v['tag'],
						choices=",".join( v['choices'] ) if 'choices' in v else '',
					)
					pks.append( obj.pk )

				# Delete all merge vars which was not defined.
				MailChimpMergeVar.objects.filter( list=self ).exclude( pk__in=pks ).delete()

				# Try to get Groupings
				pks = []
				try:
					for v in self.connection.listInterestGroupings( id=self.list_id ):
						for g in v['groups']:
							( obj, created ) = MailChimpGrouping.objects.get_or_create( list=self, group_id=v['id'], option=g['name'] )
							if obj.name != v['name']:
								obj.name = v['name']
								obj.save()
							pks.append( obj.pk )
				except TypeError:
					# listInterestGroupings will return a dict on error, that in turn will result in a TypeError when trying to be used in the for-loop. 
					pass

				MailChimpGrouping.objects.filter( list=self ).exclude( pk__in=pks ).delete()
			else:
				raise Exception( "Unknown MailChimp error." )
		except ( HTTPError, URLError ), e:
			raise MailChimpError( http_error=e )
		except KeyError, e:
			raise MailChimpError( response=res )

	def get_member_info( self, email=None ):
		"""
		Retrieve info of a member identified by the email address.
		"""
		if email:
			res = self.connection.listMemberInfo( id=self.list_id, email_address=email )
			if 'success' in res and res['success'] == 1:
				return res['data'][0]
		return {}

	def synchronize_links( self, create_missing=False ):
		"""
		Will link each mail chimp subscriber with a model object.
		"""
		if self.content_type and self.primary_key_field:
			# Get list info
			mapping = MergeVarMapping.objects.filter( list=self ).select_related()
			email_field_name = None
			for m in self.get_merge_vars():
				if m.tag == 'EMAIL':
					email_field_name = m.name
					break

			if not email_field_name:
				return

			# Iterate over members
			batch = []

			for data in self.export_members():
				if self.primary_key_field.name in data and data[self.primary_key_field.name]:
					obj = self.get_object_from_exportvars( data )
					if obj is not None:
						# Link exists so continue
						continue

				#
				# No link exists - find or create object
				#
				objdict = self.parse_export_vars( data, mapping=mapping )

				Model = self.content_type.model_class()
				if create_missing:
					obj = Model.find_or_create_object( **objdict )
				else:
					obj = Model.find_object( **objdict )

				if obj:
					batch.append( {'EMAIL': data[email_field_name], self.primary_key_field.tag : _object_identifier( obj ), } ) #'EMAIL_TYPE' : data['EMAIL_TYPE'],
				elif data[self.primary_key_field.name] != '':
					batch.append( {'EMAIL': data[email_field_name], self.primary_key_field.tag : '', } ) #'EMAIL_TYPE' : data['EMAIL_TYPE'],


				# Send updates in batches of 200	
				if len( batch ) >= 200:
					self.connection.listBatchSubscribe( id=self.list_id, batch=batch, double_optin=False, update_existing=True )
					batch = []

			# Send the last batch
			if len( batch ) > 0:
				self.connection.listBatchSubscribe( id=self.list_id, batch=batch, double_optin=False, update_existing=True )
				


	def parse_export_vars( self, data, mapping=None ):
		"""
		"""
		if mapping is None:
			mapping = MergeVarMapping.objects.filter( list=self ).select_related()

		mdict = {}
		for m in mapping:
			try:
				if m.merge_var.field_type == 'address':
					if data[m.merge_var.name]:
						mdict.update( dict( zip( ['addr1', 'addr2', 'city', 'state', 'zip', 'country'], data[m.merge_var.name].split( "  " ) ) ) )
				else:
					mdict[m.field] = data[m.merge_var.name]
			except KeyError:
				pass

		return mdict


	def export_members( self, status=None, since=None ):
		"""
		Export all MailChimp members via the export API.
		"""
		import urllib
		import urllib2
		import json

		url = 'https://%s.api.mailchimp.com/export/1.0/list/' % self.mailchimp_dc()
		params = { 'apikey' : self.api_key, 'id' : self.list_id }
		if status in ['subscribed', 'unsubscribed', 'cleaned']:
			params['status'] = status
		if since:
			params['since'] = since

		post_data = urllib.urlencode( params )
		headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		request = urllib2.Request( url, post_data, headers )
		response = urllib2.urlopen( request )

		# Read the first line (the header)
		header = json.loads( response.next() )
		# Make a generator expression which converts each line to dictionary with the header as keys
		return ( dict( zip( header, json.loads( x ) ) ) for x in response )

	def export_modelfields( self, status=None, since=None ):
		"""
		Get a list of dictionaries where each key is corresponding to a model field of the related model for the list.
		
		This method is quite heavy compared to export_members() method.
		"""
		if self.primary_key_field and self.content_type:
			members = []
			mappings = MergeVarMapping.objects.filter( list=self ).select_related()

			for m in self.export_members( status=status, since=since ):
				mdict = {}
				
				# Primary key
				if self.primary_key_field.name in m:
					mdict['pk'] = m[self.primary_key_field.name]
				
				for mapp in mappings:
					try:
						if mapp.merge_var.field_type == 'address':
							if m[mapp.merge_var.name]:
								mdict.update( dict( zip( ['addr1', 'addr2', 'city', 'state', 'zip', 'country'], m[mapp.merge_var.name].split( "  " ) ) ) )
						else:
							mdict[mapp.field] = m[mapp.merge_var.name]
					except KeyError:
						pass
				members.append( mdict )

			return members
		else:
			return None

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

	@classmethod
	def post_save_handler( cls, sender=None, instance=None, created=False, raw=False, **kwargs ):
		"""
		Start task to setup list in MailChimp (e.g. add webhooks).
		"""
		from djangoplicity.mailinglists.tasks import webhooks

		if created and not raw:
			webhooks.delay( list_id=instance.list_id )

	@classmethod
	def pre_delete_handler( cls, sender=None, instance=None, **kwargs ):
		"""
		Start task to cleanup list in MailChimp (e.g. remove webhooks).
		"""
		from djangoplicity.mailinglists.tasks import mailchimp_cleanup
		mailchimp_cleanup.delay( api_key=instance.api_key, list_id=instance.list_id )

	def __unicode__( self ):
		return self.name if self.name else self.list_id

	class Meta:
		ordering = ( 'name', )


# Connect signal handlers
post_save.connect( MailChimpList.post_save_handler, sender=MailChimpList )
pre_delete.connect( MailChimpList.pre_delete_handler, sender=MailChimpList )

MERGEVAR_DATATYPES = [
	( 'email', 'email' ),
	( 'text', 'text' ),
	( 'number', 'number' ),
	( 'radio', 'radio' ),
	( 'dropdown', 'dropdown' ),
	( 'date', 'date' ),
	( 'address', 'address' ),
	( 'phone', 'phone' ),
	( 'url', 'url' ),
	( 'imageurl', 'imageurl' ),
]

class MailChimpMergeVar( models.Model ):
	"""
	Store information about mailchimp mergevars for each list.
	"""
	list = models.ForeignKey( MailChimpList )
	name = models.CharField( max_length=255 )
	required = models.BooleanField()
	field_type = models.CharField( max_length=20, choices=MERGEVAR_DATATYPES, blank=True )
	public = models.BooleanField()
	show = models.BooleanField()
	order = models.CharField( max_length=255, blank=True )
	default = models.CharField( max_length=255, blank=True )
	size = models.CharField( max_length=255, blank=True )
	tag = models.CharField( max_length=255, blank=True )
	choices = models.TextField( blank=True )

	def __unicode__( self ):
		return "%s: %s" % ( self.list, self.name if self.field_type != 'address' else "%s (addr1,addr2,city,state,zip,country)" % self.name )
	
	class Meta:
		ordering = ['list', 'name']

class MailChimpGrouping( models.Model ):
	"""
	
	"""
	list = models.ForeignKey( MailChimpList )
	group_id = models.IntegerField( db_index=True )
	name = models.CharField( max_length=255 )
	option = models.TextField( blank=True )

	def __unicode__( self ):
		return "%s: %s" % ( self.name, self.option )

	class Meta:
		ordering = ['name', 'option']




class MergeVarMapping( models.Model ):
	list = models.ForeignKey( MailChimpList )
	merge_var = models.ForeignKey( MailChimpMergeVar )
	field = models.CharField( max_length=255 )

	def _field_list( self ):
		fields = [x.strip() for x in self.field.split( "," )]

		if len( fields ) == 6:
			return zip( ['addr1', 'addr2', 'city', 'state', 'zip', 'country'], fields )
		else:
			raise Exception( "Address type merge vars must specify 5 elements." )


	def parse_merge_var( self, params, addr_oneline=False ):
		"""
		"""
		tag = self.merge_var.tag

		if tag not in params:
			return []

		val = params[tag]

		if self.merge_var.field_type == 'address':
			try:
				res = {}
				fields = self._field_list()

				for mc_f, dj_f in fields:
					res[dj_f] = val[mc_f] if dj_f not in res else ( res[dj_f] + "  " + val[mc_f] if val[mc_f] else res[dj_f] )
				return res.items()
			except KeyError, e:
				return []
		else:
			return [( self.field, val )]


	def create_merge_var( self, obj, changes=None ):
		"""
		"""
		val = None
		field_type = self.merge_var.field_type

		if field_type == 'address':
			fields = self._field_list()

			changed = True
			if changes is not None:
				changed = False
				for f in fields:
					if f in changes:
						changed = True

			if changed:
				val = {}
				fields_done = []
				for mc_f, dj_f in fields:
					if dj_f not in fields_done:
						val[mc_f] = getattr( obj, dj_f )
						fields_done.append( dj_f )
					else:
						val[mc_f] = ''

				# Country
				if isinstance( val['country'], models.Model ):
					try:
						val['country'] = val['country'].iso_code
					except AttributeError:
						pass
		else:
			try:
				if changes is None or ( changes is not None and self.field in changes ):
					val = getattr( obj, self.field )
			except AttributeError:
				pass

		if val and field_type in ['text', 'dropdown', 'radio', 'phone', 'url', 'imageurl', 'zip']:
			val = quote( unicode( val ).encode( "utf8" ) ) # Note merge vars are sent via POST request, and apparently MailChimp library is not properly encoding the data.
	
		return ( self.merge_var.tag, val )

	def __unicode__( self ):
		return "%s -> %s" % ( self.merge_var, self.field )


class MailChimpListToken( models.Model ):
	"""
	Tokens used in get parameters to secure webhook requests 
	from MailChimp.
	"""
	list = models.ForeignKey( MailChimpList )
	uuid = models.CharField( unique=True, max_length=36, verbose_name="UUID" )
	token = models.CharField( unique=True, max_length=56 )
	expired = models.DateTimeField( null=True, blank=True )

	def get_absolute_url( self ):
		"""
		Get absolute URL to webhook. 
		"""
		if self.token and ( self.expired is None or self.expired >= datetime.now() - timedelta( minutes=10 ) ):
			baseurl = "https://%s%s" % ( Site.objects.get_current().domain, reverse( 'djangoplicity_mailinglists:mailchimp_webhook' ) )
			hookurl = "%s?%s" % ( baseurl, urlencode( self.hook_params() ) )
			return hookurl
		return None
	get_absolute_url.short_description = "Webhook URL"


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
		"""
		Find a valid token instance matching the token
		"""
		try:
			return cls.objects.filter( token=token ).filter( models.Q( expired__gte=datetime.now() - timedelta( minutes=10 ) ) | models.Q( expired__isnull=True ) ).get()
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
		return { 'token' : self.token, }


#
# More advanced stuff - configurable actions to be execute once
# contacts are added/removed from groups (e.g subscribe to mailman).
#
ACTION_EVENTS = ( 
	( 'on_subscribe', 'On subscribe' ),
	( 'on_unsubscribe', 'On unsubscribe' ),
	( 'on_upemail', 'On update email' ),
	( 'on_profile', 'On profile update' ),
	( 'on_cleaned', 'On cleaned' ),
	( 'on_campaign', 'On campaign' ),
 )

class MailChimpEventAction( EventAction ):
	"""
	Define actions to be executed when a event occurs for a list (e.g. sub, unsub, clean etc.)
	"""
	def __init__( self, *args, **kwargs ):
		super( MailChimpEventAction, self ).__init__( *args, **kwargs )
		self._meta.get_field_by_name( 'on_event' )[0]._choices = ACTION_EVENTS

	model_object = models.ForeignKey( MailChimpList )

	_key = 'djangoplicity.mailinglists.action_cache'
