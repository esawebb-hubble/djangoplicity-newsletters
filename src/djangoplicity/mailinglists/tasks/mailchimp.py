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

from celery.task import task
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import smart_unicode
from urllib import urlencode
from djangoplicity.mailinglists.models import  MailChimpList#, MailChimpSubscriberExclude


__all__ = ['mailchimp_subscribe', 'mailchimp_unsubscribe', 'mailchimp_upemail', 'mailchimp_cleaned', 'mailchimp_profile', 'mailchimp_campaign', 'webhooks', 
		'clean_tokens', 'mailchimp_send_subscribe', 'mailchimp_send_subscribe', 'mailchimp_cleanup', 'synchronize_mailchimplist', 'mailchimplist_fetch_info' ]

# ===========
# Event tasks
# ===========
def _log_webhook_action( logger, ip, user_agent, action, list, message ):
	"""
	Helper function for logging where a webhook request came from.
	"""
	logger.info( "Webhook %s action; list %s: %s; IP: %s User Agent: %s" % ( action, list, message, ip, user_agent ) )
	
def _object_identifier( obj ):
	if isinstance( obj, models.Model ):
		return ( smart_unicode( obj._meta ), smart_unicode( obj._get_pk_val(), strings_only=True ) )
	else:
		return ( None, None )
	
def _get_list( list_pk ):
	return MailChimpList.objects.get( pk = list_pk )


@task( name="mailinglists.mailchimp_subscribe", ignore_result=True )
def mailchimp_subscribe( list=None, fired_at=None, params={}, ip=None, user_agent=None ):
	"""
	User subscribed via MailChimp.
	
	- Remove from bad address if on the list and dispatch actions.
	"""
	logger = mailchimp_subscribe.get_logger()
	_log_webhook_action( logger, ip, user_agent, 'subscribe', list, "" )
	
	#
	# Deregister bad email address if exists.
	#
	from djangoplicity.mailinglists.models import BadEmailAddress
	email = params.get( 'email', '' )

	if email:
		try:
			BadEmailAddress.objects.get( email=email ).delete()
		except BadEmailAddress.DoesNotExist:
			pass
	
	from djangoplicity.mailinglists.models import MailChimpEventAction
	
	list = _get_list( list )
	
	if 'merges' in params:
		obj = list.get_object_from_mergevars( params['merges'] )
		kwargs = list.parse_merge_vars( params['merges'] )
		if obj:
			kwargs['model_identifier'], kwargs['pk'] = _object_identifier( obj )
	
		for a in MailChimpEventAction.get_actions( list, on_event='on_subscribed' ):
			a.dispatch( **kwargs )


@task( name="mailinglists.mailchimp_unsubscribe", ignore_result=True )
def mailchimp_unsubscribe( list=None, fired_at=None, params={}, ip=None, user_agent=None ):
	"""
	Email was unsubscribed from list.
	
	1) Dispatch actions.
	"""
	logger = mailchimp_unsubscribe.get_logger()
	_log_webhook_action( logger, ip, user_agent, 'unsubscribe', list, "" )
	
	from djangoplicity.mailinglists.models import MailChimpEventAction
	
	list = _get_list( list )
	obj = list.get_object_from_mergevars( params['merges'] )
	kwargs = list.parse_merge_vars( params['merges'] )
	kwargs['model_identifier'], kwargs['pk'] = _object_identifier( obj )

	for a in MailChimpEventAction.get_actions( list, on_event='on_unsubscribe' ):
		a.dispatch( **kwargs )
		

@task( name="mailinglists.mailchimp_cleaned", ignore_result=True )
def mailchimp_cleaned( list=None, fired_at=None, params={}, ip=None, user_agent=None ):
	"""
	Email was removed from MailChimp list because it was invalid.
	
	- Register bad email address and dispatch actions. If list is linked, then
	  get the object.
	"""
	logger = mailchimp_cleaned.get_logger()
	_log_webhook_action( logger, ip, user_agent, 'cleaned', list, "" )
	
	#
	# Register bad email address
	#
	from djangoplicity.mailinglists.models import BadEmailAddress
	
	email = params.get( 'email', '' )
	
	# Exclude subscriber from being put any list again, unless explicitly subscribing again.
	if email:
		badaddress, created = BadEmailAddress.objects.get_or_create( email=email )
	
	#
	# Dispatch actions
	#
	from djangoplicity.mailinglists.models import MailChimpEventAction
	
	list = _get_list( list )	
	kwargs = { 'email' : email }
	if list.content_type and list.primary_key_field:
		# List is connected, so retrieve member info via email address so we can determine
		# the object id
		try:
			obj = list.get_object_from_mergevars( list.get_member_info( email=email )['merges'] )
		except Exception:
			obj = None
		kwargs['model_identifier'], kwargs['pk'] = _object_identifier( obj )

	for a in MailChimpEventAction.get_actions( list, on_event='on_cleaned' ):
		a.dispatch( **kwargs )
	


@task( name="mailinglists.mailchimp_upemail", ignore_result=True )
def mailchimp_upemail( list=None, fired_at=None, params={}, ip=None, user_agent=None ):
	"""
	User updated his her email address.
	"""
	logger = mailchimp_upemail.get_logger()
	_log_webhook_action( logger, ip, user_agent, 'upemail', list, "" )
	
	from djangoplicity.mailinglists.models import MailChimpEventAction
	
	list = _get_list( list )
	
	for a in MailChimpEventAction.get_actions( list, on_event='on_upemail' ):
		a.dispatch( **params )

	
@task( name="mailinglists.mailchimp_profile", ignore_result=True )
def mailchimp_profile( list=None, fired_at=None, params={}, ip=None, user_agent=None ):
	"""
	User updated his her email address. First unsubscribe the old email, then 
	subscribe the new.
	
	# Perhaps change on other lists?
	"""
	logger = mailchimp_profile.get_logger()
	_log_webhook_action( logger, ip, user_agent, 'profile', list, "" )
	
	from djangoplicity.mailinglists.models import MailChimpEventAction
		
	list = _get_list( list )
	obj = list.get_object_from_mergevars( params['merges'] )
	kwargs = list.parse_merge_vars( params['merges'] )
	kwargs['model_identifier'], kwargs['pk'] = _object_identifier( obj )

	for a in MailChimpEventAction.get_actions( list, on_event='on_profile' ):
		a.dispatch( **kwargs )
		
		
@task( name="mailinglists.mailchimp_campaign", ignore_result=True )
def mailchimp_campaign( list=None, fired_at=None, params={}, ip=None, user_agent=None ):
	"""
	Cleanup mailchimp when a mailchimplist is deleted.
	"""
	logger = mailchimp_campaign.get_logger()
	_log_webhook_action( logger, ip, user_agent, 'campaign', list, "" )
	
	from djangoplicity.mailinglists.models import MailChimpEventAction
	
	for a in MailChimpEventAction.get_actions( list, on_event='on_campaign' ):
		a.dispatch( **params )
	

# ===================
# Mailman event tasks
# ===================
@task( name="mailinglists.mailchimp_send_subscribe", ignore_result=True )
def mailchimp_send_subscribe( list_name=None, email=None ):
	"""
	A user was subscribed via mailman, so send subscription to mailchimp
	"""
	logger = mailchimp_send_subscribe.get_logger()
	from djangoplicity.mailinglists.models import MailChimpList, List, MailChimpListSource

	# Find lists, that this email should be excluded from.
	excludes = [e.mailchimplist for e in MailChimpSubscriberExclude.objects.filter( subscriber__email=email )]

	# Iterate over each list, that the email needs to be include on.	
	for l in MailChimpListSource.objects.filter( list__name=list_name ).exclude( mailchimplist__in=excludes ):
		l = l.mailchimplist
		if l.synchronize:
			res = l.connection.listSubscribe( id=l.list_id, email_address=email, double_optin=False, send_welcome=False )


@task( name="mailinglists.mailchimp_send_unsubscribe", ignore_result=True )
def mailchimp_send_unsubscribe( list_name=None, email=None ):
	"""
	A user was unsubscribed via mailman, so send subscription to mailchimp
	"""
	logger = mailchimp_send_unsubscribe.get_logger()

	# Iterate over each list, that the email needs to be include on.	
	for l in MailChimpListSource.objects.filter( list__name=list_name ):
		l = l.mailchimplist
		if l.synchronize:
			res = l.connection.listUnsubscribe( id=l.list_id, delete_member=True, email_address=email, send_notify=False, send_goodbye=False )

# =============
# Misc tasks
# =============
@task( name="mailinglists.mailchimp_cleanup", ignore_result=True )
def mailchimp_cleanup( api_key=None, list_id=None ):
	"""
	Cleanup mailchimp when a mailchimplist is deleted.
	"""
	from djangoplicity.mailinglists.models import MailChimpList, MailChimpListToken
	from djangoplicity.mailinglists.exceptions import MailChimpError
	from mailsnake import MailSnake

	logger = mailchimp_cleanup.get_logger()

	try:
		connection = MailSnake( api_key )

		# Get list of all hooks
		res = connection.listWebhooks( id=list_id )

		if 'code' in res:
			raise MailChimpError( response=res )

		# Delete all hooks
		for hook in res:
			connection.listWebhookDel( id=list_id, url=hook['url'] )
	except MailChimpList.DoesNotExist:
		logger.warn( "List with list id %s does not exists" % list_id )



# =============
# Webhook tasks
# =============

@task( name="mailinglists.clean_tokens", ignore_result=True )
def clean_tokens():
	"""
	Remove invalid tokens from the database. A token is considered invalid
	10 minutes after it expired.
	"""
	from djangoplicity.mailinglists.models import MailChimpListToken
	MailChimpListToken.objects.filter( expired__lte=datetime.now() - timedelta( minutes=10 ) ).delete()


@task( name="mailinglists.webhooks", ignore_result=True )
def webhooks( list_id=None ):
	"""
	Celery task for installing webhooks for lists in MailChimp. If ``list_id`` is provided
	webhooks for only the specific list will be installed. If ``list_id`` is none, webhooks for all
	lists will be installed.
	"""
	from djangoplicity.mailinglists.models import MailChimpList, MailChimpListToken
	from djangoplicity.mailinglists.exceptions import MailChimpError

	logger = webhooks.get_logger()

	baseurl = "https://%s%s" % ( Site.objects.get_current().domain, reverse( 'djangoplicity_mailinglists:mailchimp_webhook' ) )
	errors = []

	# Check, one or many lists.	
	queryargs = { 'connected' : True, 'synchronize' : True }
	if list_id is not None:
		queryargs['list_id'] = list_id

	lists = MailChimpList.objects.filter( **queryargs )

	if len( lists ) == 0 and list_id:
		raise Exception( "List with list id %s does not exists" % list_id )

	for l in lists:
		logger.debug( "Adding/removing webhooks from list id %s" % l.list_id )

		# Create new hook for list
		try:
			# Create access token
			token = MailChimpListToken.create( l )
			hookurl = "%s?%s" % ( baseurl, urlencode( token.hook_params() ) )
			actions = { 'subscribe' : True, 'unsubscribe' : True, 'upemail' : True, 'cleaned' : True, 'profile' : True, 'campaign' : True,  }

			# Install hook in MailChimp
			res = l.connection.listWebhookAdd( id=l.list_id, url=hookurl, actions=actions, sources={ 'user' : True, 'admin' : True, 'api' : False, } )
			if res is not True:
				e = MailChimpError( response=res )
				errors.append( e )
				logger.error( unicode( e ) )

			# Expire old tokens for list
			MailChimpListToken.objects.exclude( pk=token.pk ).filter( list=l, expired__isnull=True ).update( expired=datetime.now() )
		except Exception, e:
			logger.error( unicode( e ) )
			errors.append( e )

		# Delete old hooks for list
		try:
			# Get list of all hooks
			res = l.connection.listWebhooks( id=l.list_id )
			if 'code' in res:
				raise MailChimpError( response=res )

			# Delete all hooks except the one we just installed
			for hook in res:
				if hook['url'] != hookurl:
					try:
						l.connection.listWebhookDel( id=l.list_id, url=hook['url'] )
					except Exception, e:
						logger.error( unicode( e ) )
						errors.append( e )
		except Exception, e:
			logger.error( unicode( e ) )
			errors.append( e )

	# Check for errors
	if len( errors ) > 0:
		messages = [unicode( e ) for e in errors]
		raise Exception( "Following errors occurred: %s" % "; ".join( messages ) )

	return True

# =============================
# MailChimp synchronize members
# =============================
@task( name="mailinglists.mailchimplist_fetch_info", ignore_result=True )
def mailchimplist_fetch_info( list_id=None ):
	"""
	Celery task to fetch info from MailChimp and store it locally.
	"""
	from djangoplicity.mailinglists.models import MailChimpList

	logger = mailchimplist_fetch_info.get_logger()

	try:
		
		if list_id:
			lists = MailChimpList.objects.filter( list_id=list_id )
		else:
			lists = MailChimpList.objects.filter( synchronize=True )
		
		for chimplist in lists: 
			logger.info( "Fetching info for mailchimp list %s" % chimplist.list_id )
			chimplist.fetch_info()
			chimplist.save()
	except MailChimpList.DoesNotExist:
		raise Exception( "MailChimpList %s does not exist." % list_id )



@task( name="mailinglists.synchronize_mailchimplist", ignore_result=True )
def synchronize_mailchimplist( list_id ):
	"""
	Celery task to synchronise a MailChimp list
	"""
	from djangoplicity.mailinglists.models import List, Subscription, Subscriber, MailChimpList

	logger = synchronize_mailchimplist.get_logger()

	try:
		chimplist = MailChimpList.objects.get( list_id=list_id )
		logger.debug( "Found list %s" % list_id )
	except MailChimpList.DoesNotExist:
		raise Exception( "MailChimpList %s does not exist." % list_id )


	# Synchronisation enabled for list?
	if not chimplist.synchronize:
		return

	( subscribe_emails, unsubscribe_emails ) = chimplist.outgoing_changes()

	#
	# Send subscriptions in batches of 1k
	#
	if len( subscribe_emails ) > 0:
		BATCH_SIZE = 1000
	
		results = []
		batch = [{ 'EMAIL' : email, 'EMAIL_TYPE' : 'html', }  for email in subscribe_emails]
		
		while len( batch ) > 0:
			batch_part = batch[:BATCH_SIZE]
			res = chimplist.connection.listBatchSubscribe( id=chimplist.list_id, batch=batch_part, double_optin=False )
			# TODO check result
			results.append( res )
			batch = batch[BATCH_SIZE:]
	
		combined_result = {
			'add_count' : 0,
			'update_count' : 0,
			'error_count' : 0,
			'errors' : [],
		}
		
		# Combine result of all batches
		for r in results:
			for k in combined_result.keys():
				if k in r:
					combined_result[k] += r[k]
	
	#
	# Send unsubscribe emails
	#
	if len( unsubscribe_emails ) > 0:
		emails = list( unsubscribe_emails )
		res = chimplist.connection.listBatchUnsubscribe( id=chimplist.list_id, emails=emails, delete=True, send_goodbye=False, send_notify=False )
