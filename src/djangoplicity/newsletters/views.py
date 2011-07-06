# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#	* Redistributions of source code must retain the above copyright
#	  notice, this list of conditions and the following disclaimer.
#
#	* Redistributions in binary form must reproduce the above copyright
#	  notice, this list of conditions and the following disclaimer in the
#	  documentation and/or other materials provided with the distribution.
#
#	* Neither the name of the European Southern Observatory nor the names 
#	  of its contributors may be used to endorse or promote products derived
#	  from this software without specific prior written permission.
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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from djangoplicity.newsletters.models import MailChimpListToken, MailChimpList, Subscriber
from djangoplicity.newsletters.tasks import mailchimp_subscribe, mailchimp_unsubscribe, mailchimp_upemail, mailchimp_cleaned
from django.http import Http404, HttpResponse


def newsletters_detail ( request ):

	tplname = request.GET.get('template','main')
	
	ctx = {}
	resp =  render_to_response( 'newsletters/%s.html' % tplname, ctx, RequestContext( request, {} ) )

	subject, from_email = '[NEWSLETTER TEST] ESO Outreach & Education Newsletter - July 2011', 'lnielsen@eso.org'
	text_content = 'text content only'
	html_content = resp.content
	#to = ['lnielsen@eso.org','osandu@eso.org','lars@eso.org','andreroquette.eso@googlemail.com']
	to = ['lnielsen@eso.org', ]
	msg = EmailMultiAlternatives( subject, text_content, from_email, to )
	msg.attach_alternative( html_content, "text/html" )
	#msg.send()
	
	return resp


def subscribe_event( request, list, fired_at ):
	"""
	"type": "subscribe", 
	"fired_at": "2009-03-26 21:35:57", 
	"data[id]": "8a25ff1d98", 
	"data[list_id]": "a6b5da1054",
	"data[email]": "api@mailchimp.com", 
	"data[email_type]": "html", 
	"data[merges][EMAIL]": "api@mailchimp.com", 
	"data[merges][FNAME]": "MailChimp", 
	"data[merges][LNAME]": "API", 
	"data[merges][INTERESTS]": "Group1,Group2", 
	"data[ip_opt]": "10.20.10.30", 
	"data[ip_signup]": "10.20.10.30"
	
	
	exists on default list:
	- do nothing
	
	exists on secondary mailman list but not default:
	- remove email from exclude lists
	- add to default mailman list.
	
	does not exists on mailman list:
	- subscribe to default mailman list
	"""
	mailchimp_subscribe.delay( 
		list=list.pk,
		fired_at=fired_at,
		email=request.POST['data[email]'],
	)
	return HttpResponse( "" )

	
def unsubscribe_event( request, list, fired_at ):
	"""
	"type": "unsubscribe", 
	"fired_at": "2009-03-26 21:40:57",  
	"data[id]": "8a25ff1d98", 
	"data[list_id]": "a6b5da1054",
	"data[email]": "api+unsub@mailchimp.com", 
	"data[email_type]": "html", 
	"data[merges][EMAIL]": "api+unsub@mailchimp.com", 
	"data[merges][FNAME]": "MailChimp", 
	"data[merges][LNAME]": "API", 
	"data[merges][INTERESTS]": "Group1,Group2", 
	"data[ip_opt]": "10.20.10.30",
	"data[campaign_id]": "cb398d21d2",
	"data[reason]": "hard"
	
	exists on default mailman list:
	- remove from default list

	exists on secondary mailman list:
	- add to exclude 
	
	does not exists on mailman list:
	- subscribe to default mailman list
	"""
	mailchimp_unsubscribe.delay( 
		list=list.pk,
		fired_at=fired_at,
		email=request.POST['data[email]'],
	)
	return HttpResponse( "" )
	
def profile_event( request, list, fired_at ):
	"""
	"type": "profile", 
	"fired_at": "2009-03-26 21:31:21", 
	"data[id]": "8a25ff1d98", 
	"data[list_id]": "a6b5da1054",
	"data[email]": "api@mailchimp.com", 
	"data[email_type]": "html", 
	"data[merges][EMAIL]": "api@mailchimp.com", 
	"data[merges][FNAME]": "MailChimp", 
	"data[merges][LNAME]": "API", 
	"data[merges][INTERESTS]": "Group1,Group2", 
	"data[ip_opt]": "10.20.10.30"
	"""
	return HttpResponse( "" )
	
def upemail_event( request, list, fired_at ):
	"""
	"type": "upemail", 
	"fired_at": "2009-03-26\ 22:15:09", 
	"data[list_id]": "a6b5da1054",
	"data[new_id]": "51da8c3259", 
	"data[new_email]": "api+new@mailchimp.com", 
	"data[old_email]": "api+old@mailchimp.com"
	"""
	mailchimp_upemail.delay( 
		list=list.pk,
		fired_at=fired_at,
		new_email=request.POST['data[new_email]'],
		old_email=request.POST['data[old_email]'],
	)
	return HttpResponse( "" )

def cleaned_event( request, list, fired_at ):
	"""
	"type": "cleaned", 
	"fired_at": "2009-03-26 22:01:00", 
	"data[list_id]": "a6b5da1054",
	"data[campaign_id]": "4fjk2ma9xd",
	"data[reason]": "hard",
	"data[email]": "api+cleaned@mailchimp.com"
	"""
	mailchimp_cleaned.delay( 
		list=list.pk,
		fired_at=fired_at,
		email=request.POST['data[email]'],
	)
	return HttpResponse( "" )


EVENT_HANDLERS = {
	'subscribe' : subscribe_event,
	'unsubscribe' : unsubscribe_event,
	'upemail' : upemail_event,
	'cleaned' : cleaned_event,
}

def mailchimp_webhook( request, require_secure=True ):
	"""
	MailChimp webhook view (see http://apidocs.mailchimp.com/webhooks/)
	
	Validates the request to ensure it is from MailChimp, and delegates
	event processing to event handlers. 
	
	Validation checks::
	  * POST request
	  * HTTPS request
	  * Validate token
	  * Validate that list exists
	  
	A request to mailchimp_webook must be completed within 15 seconds, thus 
	event handlers should only gather the data they need, and send the rest 
	for background processing.
	"""
	# Check expected request type
	if request.method != "POST":
		raise Http404
	
	if not request.is_secure():
		if require_secure:
			raise Http404

	# Get input values
	try:
		token = request.GET['token']
		uuid = request.GET['uuid']
		
		type = request.POST['type']
		fired_at = request.POST['fired_at']
		list_id = request.POST['data[list_id]']
	except KeyError:
		raise Http404
	
	# Check type 
	if type not in ['subscribe', 'unsubscribe', 'profile', 'upemail', 'cleaned']:
		raise Http404
	
	# Check token
	if not MailChimpListToken.validate_token( list_id, uuid, token ):
		raise Http404
	
	# Check list
	try:
		list = MailChimpList.objects.get( list_id=list_id )
	except MailChimpList.DoesNotExist:
		raise Http404
	
	# Get event handler
	try:
		view = EVENT_HANDLERS[type]
	except KeyError:
		raise Http404
	
	# Pass to event handler for processing.
	return view( request, list, fired_at )