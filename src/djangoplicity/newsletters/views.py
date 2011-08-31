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


from django.http import Http404, HttpResponse
from djangoplicity.newsletters.models import Newsletter


#def newsletter_liverender( request, pk ):
#	"""
#	Render a newsletter
#	"""
#	nl = Newsletter.objects.get( pk = pk )
#	nl.render()
#	
#	if request.GET.get( 'text', False ):
#		response = HttpResponse( nl.text, mimetype="text/plain; charset=utf8" )
#		return response
#	else:
#		return HttpResponse( nl.html, mimetype="text/html" )
#
#def newsletters_detail ( request ):
#
#	tplname = request.GET.get('template','main')
#	
#	from djangoplicity.announcements.models import Announcement
#	from djangoplicity.releases.models import Release
#	from djangoplicity.media.models import Video, Image, PictureOfTheWeek
#	
#	ctx = {
#		'announcements' : Announcement.objects.filter( id__in=['ann11048','ann11047','ann11043','ann11045','ann1067','ann11018','ann11043','ann11012','ann11043','ann1097','ann1086','ann1007',]).order_by('-release_date'),
#		'esocasts' :  Video.objects.filter( id__in=['eso1122a', 'eso1120a', 'eso1119a', ] ).order_by('-release_date'),
#		'mainimage' : PictureOfTheWeek.objects.get( id='potw1128').image,
#		'potws' : PictureOfTheWeek.objects.filter( id__in=['potw1127','potw1126', 'potw1125', 'potw1124', 'potw1123', ] ).order_by('-release_date'),
#		'releases' : Release.objects.filter( id__in=['eso1123','eso1122','eso1121','eso1120','eso1119','eso1118',]).order_by('-release_date'),
#		'newoneso' : [
#			{'title' : 'List of ESO Exhibitions updated', 'link' : 'http://www.eso.org/public/events/exhibitions.html'},
#			{'title' : 'New APOD: Alpha Centauri: The Closest Star System', 'link' : 'http://apod.nasa.gov/apod/ap110703.html'},
#			{'title' : 'New APOD: Star Factory Messier 17', 'link' : 'http://apod.nasa.gov/apod/ap110630.html'},
#			{'title' : 'New  APOD: Stardust and Betelgeuse', 'link' : 'http://apod.nasa.gov/apod/ap110628.html'},
#			{'title' : 'New APOD: The Great Carina Nebula', 'link' : 'http://apod.nasa.gov/apod/ap110609.html'},
#			{'title' : 'VST new pages', 'link' : 'http://www.eso.org/public/teles-instr/surveytelescopes/vst.html'},
#			{'title' : 'New APOD: Earth Rotating Under Very Large Telescopes', 'link' : 'http://apod.nasa.gov/apod/ap110601.html'},
#			{'title' : 'New Page: Astronomy Communication Resources', 'link' : 'http://www.eso.org/public/outreach/communication-resources.html'},
#		],
#		'ongoing_events' : [
#			{'title' : 'The Eye 3D School Screenings', 'link' : 'http://www.eso.org/public/events/special-evt/theeye/theeye3dschool.html' },
#			{'title' : 'Café & Kosmos in Munich', 'link' : 'http://www.eso.org/public/events/special-evt/cafe-and-kosmos.html' },
#		],
#		'events' : [
#			{'dates' : '10 &mdash; 14 October 2011', 'title' : '<a href="http://www.communicatingastronomy.org/cap2011/index.html" target="_blank">Communicating Astronomy with the Public 2011 (CAP 2011), Beijing, China</a>'},
#			{'dates' : '15 October 2011', 'title' : '<a href="http://www.forschung-garching.de/">Open House Day (Tag der offenen Tur). Campus Garching, Germany.</a>'},
#		],
#		'exhibitions' : [
#			{ 'dates' : '4 &mdash; 8 July 2011', 'title' : 'Joint European National Astronomy Meeting (<a href="http://jenam2011.org/conf/" target="_blank">JENAM 2011</a>), St.Petersburg, Russia.' },
#			{ 'dates' : '10 &mdash; 15 July 2011', 'title' : '63rd Annual Meeting of the&nbsp;Brazilian Society for the Progress of Science (<a href="http://www.sbpcnet.org.br/site/home/" target="_blank">Sociedade Brasileira para o Progresso da Ci&ecirc;ncia, SBPC</a>), Goiania, Brazil.' },
#			{ 'dates' : '16 July 2011', 'title' : '&quot;<a href="http://www.gemini.edu/node/11609">Astroday</a>&quot;, Universidad de La Serena, La Serena, Chile.' },
#			{ 'dates' : '18 July &mdash; 30 August 2011', 'title' : 'Exhibition at the National Congress, Bras&iacute;lia, Brazil.' },
#			{ 'dates' : '20 July &mdash; 20 September 2011', 'title' : 'Exposition &quot;The World At Night&quot;, Planetario Galileo Galilei, Buenos Aires, Argentina.' },
#		],
#		'editorial' : """
#<p>Dear Friends,</p>
#
#<p>The ESO education and Public Outreach Department (ePOD) are proud to present the very first edition of the ESO Outreach Community Newsletter! It is our pleasure to share with you, as colleagues, our endeavours to bring astronomy closer to people.</p>
#
#<p>We hope that you will find useful tools, products and opportunities in this monthly electronic newsletter to help you in your outreach work and also that our outreach efforts will inspire new ideas for your own activities. Among the highlights of this issue are CAP 2011 in China and the latest issue of CAPjournal.</p>
#
#<p>We have merged several of the contacts that were already in our database of mailing lists from previous collaborations. Therefore our apologies if you receive this newsletter on more than one e-mail account. You can unsubscribe at any time <a href="*|UNSUB|*">here</a>, but we hope that you will remain part of our outreach community. We promise to not let you down!</p>
#
#<p>If the ESO Outreach Community Newsletter is not directly relevant to you, we have several other options that might be of interest:
#<ul>
#<li><strong>ESO Media Newsletter</strong> for members of the press only (weekly);</li>
#<li><strong>ESO News</strong> for anyone interested in astronomy news and pictures from ESO (weekly);</li>
#<li><strong>ESOshop Newsletter</strong> for those interested in our merchandise (monthly);</li>
#<li><strong>ESO Broadcasters Newsletter</strong> for professionals interested in ESO video material and footage (occasionally).</li>
#</ul>
#<p>
#<img src="http://www.eso.org/public/outreach/department/images/lars_christensen.jpg" width="122" style="float: left; margin: 10px;"/>
#</p>
#
#<p>You can subscribe to them <a href="http://www.eso.org/public/outreach/newsletters.html">here</a>.</p>
#
#<p>If you are interested in occasionally receiving outreach products via snail mail and collaborating closely with ePOD, do please consider providing a complete postal address and choosing the category you qualify for in <a href="*|UPDATE_PROFILE|*">this form</a>.</p>
#
#<p>Let’s together reach new heights in astronomy,</p>
#
#<p>Lars Lindberg Christensen (lars@eso.org)<br />
#Head ESO education and Public Outreach Department<br /><br /><br /><br /></p>		
#""",
#
#	}
#	
#	
#	resp =  render_to_response( 'newsletters/%s.html' % tplname, ctx, RequestContext( request, {} ) )
#
#	subject, from_email = '[NEWSLETTER TEST] ESO Outreach & Education Newsletter - July 2011', 'lnielsen@eso.org'
#	text_content = 'text content only'
#	html_content = resp.content
#	#to = ['lnielsen@eso.org','osandu@eso.org','lars@eso.org','andreroquette.eso@googlemail.com']
#	to = ['lnielsen@eso.org', ]
#	msg = EmailMultiAlternatives( subject, text_content, from_email, to )
#	msg.attach_alternative( html_content, "text/html" )
#	#msg.send()
#	
#	return resp
#
#
#		