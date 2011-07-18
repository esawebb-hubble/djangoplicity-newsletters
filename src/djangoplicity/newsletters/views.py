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
	
	from djangoplicity.announcements.models import Announcement
	from djangoplicity.releases.models import Release
	from djangoplicity.media.models import Video, Image, PictureOfTheWeek
	
	ctx = {
		'announcements' : Announcement.objects.filter( id__in=['ann11048','ann11047','ann11043','ann11045','ann1067','ann11018','ann11043','ann11012','ann11043','ann1097','ann1086','ann1007',]).order_by('-release_date'),
		'esocasts' :  Video.objects.filter( id__in=['eso1122a', 'eso1120a', 'eso1119a', ] ).order_by('-release_date'),
		'mainimage' : PictureOfTheWeek.objects.get( id='potw1128').image,
		'potws' : PictureOfTheWeek.objects.filter( id__in=['potw1127','potw1126', 'potw1125', 'potw1124', 'potw1123', ] ).order_by('-release_date'),
		'releases' : Release.objects.filter( id__in=['eso1123','eso1122','eso1121','eso1120','eso1119','eso1118',]).order_by('-release_date'),
		'newoneso' : [
			{'title' : 'List of ESO Exhibitions updated', 'link' : 'http://www.eso.org/public/events/exhibitions.html'},
			{'title' : 'New APOD: Alpha Centauri: The Closest Star System', 'link' : 'http://apod.nasa.gov/apod/ap110703.html'},
			{'title' : 'New APOD: Star Factory Messier 17', 'link' : 'http://apod.nasa.gov/apod/ap110630.html'},
			{'title' : 'New  APOD: Stardust and Betelgeuse', 'link' : 'http://apod.nasa.gov/apod/ap110628.html'},
			{'title' : 'New APOD: The Great Carina Nebula', 'link' : 'http://apod.nasa.gov/apod/ap110609.html'},
			{'title' : 'VST new pages', 'link' : 'http://www.eso.org/public/teles-instr/surveytelescopes/vst.html'},
			{'title' : 'New APOD: Earth Rotating Under Very Large Telescopes', 'link' : 'http://apod.nasa.gov/apod/ap110601.html'},
			{'title' : 'New Page: Astronomy Communication Resources', 'link' : 'http://www.eso.org/public/outreach/communication-resources.html'},
		],
		'ongoing_events' : [
			{'title' : 'The Eye 3D School Screenings', 'link' : 'http://www.eso.org/public/events/special-evt/theeye/theeye3dschool.html' },
			{'title' : 'Café & Kosmos in Munich', 'link' : 'http://www.eso.org/public/events/special-evt/cafe-and-kosmos.html' },
		],
		'events' : [
			{'dates' : '10 &mdash; 14 October 2011', 'title' : '<a href="http://www.communicatingastronomy.org/cap2011/index.html" target="_blank">Communicating Astronomy with the Public 2011 (CAP 2011), Beijing, China</a>'},
			{'dates' : '15 October 2011', 'title' : '<a href="http://www.forschung-garching.de/">Open House Day (Tag der offenen Tur). Campus Garching, Germany.</a>'},
		],
		'exhibitions' : [
			{ 'dates' : '4 &mdash; 8 July 2011', 'title' : 'Joint European National Astronomy Meeting (<a href="http://jenam2011.org/conf/" target="_blank">JENAM 2011</a>), St.Petersburg, Russia.' },
			{ 'dates' : '10 &mdash; 15 July 2011', 'title' : '63rd Annual Meeting of the&nbsp;Brazilian Society for the Progress of Science (<a href="http://www.sbpcnet.org.br/site/home/" target="_blank">Sociedade Brasileira para o Progresso da Ci&ecirc;ncia, SBPC</a>), Goiania, Brazil.' },
			{ 'dates' : '16 July 2011', 'title' : '&quot;<a href="http://www.gemini.edu/node/11609">Astroday</a>&quot;, Universidad de La Serena, La Serena, Chile.' },
			{ 'dates' : '18 July &mdash; 30 August 2011', 'title' : 'Exhibition at the National Congress, Bras&iacute;lia, Brazil.' },
			{ 'dates' : '20 July &mdash; 20 September 2011', 'title' : 'Exposition &quot;The World At Night&quot;, Planetario Galileo Galilei, Buenos Aires, Argentina.' },
		],
		'editorial' : """
<p>Dear Friends,</p>

<p>The ESO education and Public Outreach Department (ePOD) are proud to present the very first edition of the ESO Outreach Community Newsletter! It is our pleasure to share with you, as colleagues, our endeavours to bring astronomy closer to people.</p>

<p>We hope that you will find useful tools, products and opportunities in this monthly electronic newsletter to help you in your outreach work and also that our outreach efforts will inspire new ideas for your own activities. Among the highlights of this issue are CAP 2011 in China and the latest issue of CAPjournal.</p>

<p>We have merged several of the contacts that were already in our database of mailing lists from previous collaborations. Therefore our apologies if you receive this newsletter on more than one e-mail account. You can unsubscribe at any time <a href="*|UNSUB|*">here</a>, but we hope that you will remain part of our outreach community. We promise to not let you down!</p>

<p>If the ESO Outreach Community Newsletter is not directly relevant to you, we have several other options that might be of interest:
<ul>
<li><strong>ESO Media Newsletter</strong> for members of the press only (weekly);</li>
<li><strong>ESO News</strong> for anyone interested in astronomy news and pictures from ESO (weekly);</li>
<li><strong>ESOshop Newsletter</strong> for those interested in our merchandise (monthly);</li>
<li><strong>ESO Broadcasters Newsletter</strong> for professionals interested in ESO video material and footage (occasionally).</li>
</ul>
<p>
<img src="http://www.eso.org/public/outreach/department/images/lars_christensen.jpg" width="122" style="float: left; margin: 10px;"/>
</p>

<p>You can subscribe to them <a href="http://www.eso.org/public/outreach/newsletters.html">here</a>.</p>

<p>If you are interested in occasionally receiving outreach products via snail mail and collaborating closely with ePOD, do please consider providing a complete postal address and choosing the category you qualify for in <a href="*|UPDATE_PROFILE|*">this form</a>.</p>

<p>Let’s together reach new heights in astronomy,</p>

<p>Lars Lindberg Christensen (lars@eso.org)<br />
Head ESO education and Public Outreach Department<br /><br /><br /><br /></p>		
""",

	}
	
	
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


def subscribe_event( request, list, fired_at, **kwargs ):
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
		**kwargs
	)
	return HttpResponse( "" )

	
def unsubscribe_event( request, list, fired_at, **kwargs ):
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
		**kwargs
	)
	return HttpResponse( "" )
	
def profile_event( request, list, fired_at, **kwargs ):
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
	
def upemail_event( request, list, fired_at, **kwargs ):
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
		**kwargs
	)
	return HttpResponse( "" )

def cleaned_event( request, list, fired_at, **kwargs ):
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
		**kwargs
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
	return view( request, list, fired_at, ip=request.META['REMOTE_ADDR'], user_agent=request.META.get('HTTP_USER_AGENT',''), )