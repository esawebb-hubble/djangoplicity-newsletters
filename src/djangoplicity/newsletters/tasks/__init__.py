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
from djangoplicity.mailinglists.models import MailChimpList
from djangoplicity.newsletters.models import Newsletter
	
campaign_id = '46548cd537'

def send_campaign():
	
	
	ml = MailChimpList.objects.get( list_id='c99dfddf3f' )
	
	#ml.connection.campaignSendTest( cid=campaign_id, test_emails=['lnielsen@eso.org'] )
	#ml.connection.campaignSendNow( cid=campaign_id )
	
	

def upload_campaign():
	nl = Newsletter.objects.get( pk = 10 )
	ml = MailChimpList.objects.get( list_id='c99dfddf3f' )
	
	campaigns = ml.connection.campaigns( filters={ 'list_id' : ml.list_id, 'campaign_id' : '' } )
	
	nl.render()
	
	if 'total' in campaigns and campaigns['total'] > 0:
		val = ml.connection.campaignUpdate( cid = campaign_id, name = 'subject', value = nl.subject )
		print val
		val = ml.connection.campaignUpdate( cid = campaign_id, name = 'from_email', value = nl.from_email )
		print val
		val = ml.connection.campaignUpdate( cid = campaign_id, name = 'from_name', value = nl.from_name )
		print val
		val = ml.connection.campaignUpdate( cid = campaign_id, name = 'title', value = nl.subject )
		print val
		val = ml.connection.campaignUpdate( cid = campaign_id, name = 'subject', value = nl.subject )
		print val
		val = ml.connection.campaignUpdate( cid = campaign_id, name = 'content', value = { 'html' : nl.html, 'text' : nl.text } )
		print val
	else:
		val = ml.connection.campaignCreate(
			type = 'regular',
			options = {
				'list_id' : ml.list_id,
				'subject' : nl.subject,
				'from_email' : nl.from_email,
				'from_name' : nl.from_name,
				'tracking' : { 'opens' : True, 'html_clicks' : True, 'text_clicks' : False },
				'title' : nl.subject,
				'authenticate' : True,
				'auto_footer' : False,
				'inline_css' : True,
				'fb_comments' : True,
			},
			content = {
				'html' : nl.html,
				'text' : nl.text,
			}
		 )
		print val