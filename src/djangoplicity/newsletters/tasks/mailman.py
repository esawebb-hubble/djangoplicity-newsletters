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


__all__ = ['clean_subscribers', 'synchronize_mailman', 'mailman_send_unsubscribe', 'mailman_send_subscribe']


@task( name='newsletters.clean_subscribers', ignore_result=True )
def clean_subscribers():
	"""
	Remove subscribers which no longer have any subscriptions or is on an exclude list.
	"""
	from djangoplicity.newsletters.models import Subscription, MailChimpSubscriberExclude
	
	logger = clean_subscribers.get_logger()

	#TODO - Remove all subscribers not having a subscription nor being excluded.
	

@task( name="newsletters.synchronize_mailman", ignore_result=True )
def synchronize_mailman( list_name ):
	"""
	Task to synchronise a mailman list into djangoplicity.
	"""
	from djangoplicity.newsletters.models import List, Subscriber, BadEmailAddress
	
	logger = synchronize_mailman.get_logger()

	try:
		list = List.objects.get( name=list_name )
		list.last_sync = datetime.now()
		list.save()
	except List.DoesNotExist:
		raise Exception( "List %s does not exist." % list_name )

	logger.debug( "Found list %s" % list_name )
	
	( subscribe_emails, unsubscribe_emails, current_list_subscribers, mailman_unsubscribe_emails ) = list.incoming_changes()
	
	existing_subscribers = dict( [( s.email, s ) for s in Subscriber.objects.filter( email__in=subscribe_emails )] )
	current_list_subscribers = dict( [( s.email, s ) for s in current_list_subscribers] )
	
	# Subscribe to django
	for e in subscribe_emails:
		if e in existing_subscribers:
			subscriber = existing_subscribers[e]
		else:
			subscriber, created = Subscriber.objects.get_or_create( email=e )

		logger.info( "Subscribe %s to %s" % ( subscriber.email, list.name ) )
		list.subscribe( subscriber, source=list )

	# Unsubscribe from django
	for e in unsubscribe_emails:
		if e in current_list_subscribers:
			subscriber = current_list_subscribers[e]
			
			logger.info( "Unsubscribe %s from %s" % ( subscriber.email, list.name ) )
			list.unsubscribe( subscriber, source=list )
	
	# Unsubscribe from mailman
	for e in mailman_unsubscribe_emails:
		mailman_send_unsubscribe.delay( list_name, e )
			

@task( name="newsletters.mailman_send_subscribe", ignore_result=True )
def mailman_send_subscribe( list_name, email ):
	"""
	Task to subscribe an email to a mailman list. Task is executed
	when e.g. a person subscribes via e.g. mailchimp.
	"""
	from djangoplicity.newsletters.models import List
	
	logger = mailman_send_unsubscribe.get_logger()
	
	list = List.objects.get( name=list_name )
	list.mailman.subscribe( email )
	
	logger.info( "Subscribed %s to mailman list %s" % ( email, list_name ) )
		
	
@task( name="newsletters.mailman_send_unsubscribe", ignore_result=True )
def mailman_send_unsubscribe( list_name, email ):
	"""
	Task to subscribe an email to a mailman list. Task is executed
	when e.g. a person subscribes via e.g. mailchimp.
	"""
	from djangoplicity.newsletters.models import List
	
	logger = mailman_send_unsubscribe.get_logger()
	
	list = List.objects.get( name=list_name )
	list.mailman.unsubscribe( email )
	
	logger.info( "Unsubscribed %s from mailman list %s" % ( email, list_name ) )


		
	
	
	