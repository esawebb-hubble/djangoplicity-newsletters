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
from urllib import urlencode
from djangoplicity.newsletters.models import ListSynchronization

@task( name="newsletters.synchronize_mailman", ignore_result=True )
def synchronize_mailman( list_name ):
	"""
	Task to synchronize a mailman list with djangoplicity, additionally keeps a record
	log which allows synchronizing djangoplicity lists.
	"""
	from djangoplicity.newsletters.models import List, Subscription, Subscriber, ListActionLog
	from django_mailman.models import List as MailmanList

	logger = synchronize_mailman.get_logger()
	try:
		list = List.objects.get( name=list_name )
	except List.DoesNotExist:
		raise Exception( "List %s does not exist." % list_name )

	logger.debug( "Found list %s" % list_name )

	mailmanlist = MailmanList( name=list.name, password=list.password, email="%s@eso.org" % list.name, main_url="http://www.eso.org/lists" )
	mailman_members = mailmanlist.get_all_members()

	if mailman_members:
		mailman_names, mailman_emails = zip( *mailman_members )
		mailman_emails = set( mailman_emails )
	else:
		mailman_names, mailman_emails = [], set( [] )

	current_subscribers = list.subscribers.all()
	current_emails = set( [s.email for s in current_subscribers] )

	add_emails = mailman_emails - current_emails
	remove_emails = current_emails - mailman_emails

	existing_subscribers = dict( [( s.email, s ) for s in Subscriber.objects.filter( email__in=add_emails )] )
	current_subscribers = dict( [( s.email, s ) for s in current_subscribers] )

	for e in add_emails:
		if e in existing_subscribers:
			subscriber = existing_subscribers[e]
		else:
			subscriber = Subscriber( email=e )
			subscriber.save()

		sub = Subscription( list=list, subscriber=subscriber )
		sub.save()
		
		log = ListActionLog( list=list, subscriber=subscriber, action='sub' )
		log.save()

	for e in remove_emails:
		if e in current_subscribers:
			subscriber = current_subscribers[e]
			list.subscribers.remove( subscriber )
			
			log = ListActionLog( list=list, subscriber=subscriber, action='unsub' )
			log.save()



@task( name="newsletters.synchronize_list", ignore_result=True )
def synchronize_list( list_name ):
	"""
	
	"""
	from djangoplicity.newsletters.models import List, Subscription, Subscriber, ListSynchronization, ListActionLog
	from django_mailman.models import List as MailmanList

	logger = synchronize_list.get_logger()
	
	list = List.objects.get( name=list_name )
	
	destination_lists = ListSynchronization.objects.filter( source=list )
	
	actions = ListActionLog.objects.filter( list_source_lists=list )
	
	for l in destination_lists:
		subscrib
	
	
	
	

@task( name="newsletters.synchronize_mailchimplist", ignore_result=True )
def synchronize_mailchimplist( list_id ):
	"""
	Celery task to synchronize a MailChimp list
	"""
	from djangoplicity.newsletters.models import List, Subscription, Subscriber, MailChimpList

	logger = synchronize_mailchimplist.get_logger()

	try:
		chimplist = MailChimpList.objects.get( list_id=list_id )
		logger.debug( "Found list %s" % list_id )
	except MailChimpList.DoesNotExist:
		raise Exception( "MailChimpList %s does not exist." % list_id )

	#
	# Send subscriptions in batches of 1k
	#
	BATCH_SIZE = 1000

	results = []
	batch = [{ 'EMAIL' : s.email, 'EMAIL_TYPE' : 'html', }  for s in chimplist.get_source_subscribers()]

	while len( batch ) > 0:
		batch_part = batch[:BATCH_SIZE]
		res = chimplist.connection.listBatchSubscribe( id=chimplist.list_id, batch=batch_part, double_optin=False, )
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

	# Todo:
	# - handle errors for subscriptions (e.g subscribers that was not added due to generic accounts).
	# - log errors.
	# - general logging of actions.
	# - don't subscribe people who have requested to be removed from mailchimp.

	# Todo add subscribers/uns from 

	#combined_result

@task( name="newsletters.clean_tokens", ignore_result=True )
def clean_tokens():
	"""
	Remove invalid tokens from the database. A token is considered invalid
	10 minutes after it expired.
	"""
	from djangoplicity.newsletters.models import MailChimpListToken
	MailChimpListToken.objects.filter( expired__lte=datetime.now() - timedelta( minutes=10 ) ).delete()


@task( name="newsletters.webhooks", ignore_result=True )
def webhooks( list_id=None ):
	"""
	Celery task for installing webhooks for lists in MailChimp. If ``list_id`` is provided
	webhooks for only the specific list will be installed. If ``list_id`` is none, webhooks for all
	lists will be installed.
	"""
	from djangoplicity.newsletters.models import MailChimpList, MailChimpListToken
	from djangoplicity.newsletters.exceptions import MailChimpError
	
	logger = webhooks.get_logger()

	baseurl = "https://%s%s" % ( Site.get_current_site().domain, reverse( 'djangoplicity_newsletters:mailchimp_webhook' ) )
	errors = []
	
	# Check, one or many lists.	
	queryargs = { 'connected' : True }
	if list_id is not None:
		queryargs['list_id'] = list_id

	lists = MailChimpList.objects.filter( queryargs )
	
	if len(lists) == 0 and list_id:
		raise Exception( "List with list id %s does not exists" % list_id )
	
	for l in lists:
		logger.debug( "Adding/removing webhooks from list id %s" % l.list_id )

		# Create new hook for list
		try:
			# Create access token
			token = MailChimpListToken.create( l )
			hookurl = "%s?%s" % ( baseurl, urlencode( token.hook_params() ) )
			actions = { 'subscribe' : True, 'unsubscribe' : True, 'upemail' : True, 'cleaned' : True, 'profile' : False }

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
			res = l.conneciton.listWebhooks( id=l.list_id )
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













