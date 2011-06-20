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

from django.test import TestCase, RequestFactory


class WebHooksTest( TestCase ):
	def setUp( self ):
		self.factory = RequestFactory()

		from djangoplicity.newsletters.models import MailChimpList, MailChimpListToken
		from urllib import urlencode

		list = MailChimpList( api_key="not_valid", list_id="not_valid", connected=True )
		list.save()

		token = MailChimpListToken.create( list )

		self.list = list
		self.token = token
		self.params = urlencode( token.hook_params() )
		
	def _mailchimp_webhook( self, data ):
		from djangoplicity.newsletters.views import mailchimp_webhook
		request = self.factory.post( '/webhook/?%s' % self.params, data=data )
		return mailchimp_webhook( request, require_secure=False )

	def test_subscribe( self ):
		data = {
			"type": "subscribe",
			"fired_at": "2009-03-26 21:35:57",
			"data[id]": "8a25ff1d98",
			"data[list_id]": self.list.list_id,
			"data[email]": "api@mailchimp.com",
			"data[email_type]": "html",
			"data[merges][EMAIL]": "api@mailchimp.com",
			"data[merges][FNAME]": "MailChimp",
			"data[merges][LNAME]": "API",
			"data[merges][INTERESTS]": "Group1,Group2",
			"data[ip_opt]": "10.20.10.30",
			"data[ip_signup]": "10.20.10.30",
		}
		response = self._mailchimp_webhook( data )
		self.assertEqual( response.status_code, 200 )


	def test_unsubscribe(self):
		data = {
			"type": "unsubscribe", 
			"fired_at": "2009-03-26 21:40:57",  
			"data[id]": "8a25ff1d98", 
			"data[list_id]": self.list.list_id,
			"data[email]": "api+unsub@mailchimp.com", 
			"data[email_type]": "html", 
			"data[merges][EMAIL]": "api+unsub@mailchimp.com", 
			"data[merges][FNAME]": "MailChimp", 
			"data[merges][LNAME]": "API", 
			"data[merges][INTERESTS]": "Group1,Group2", 
			"data[ip_opt]": "10.20.10.30",
			"data[campaign_id]": "cb398d21d2",
			"data[reason]": "hard"
		}
		response = self._mailchimp_webhook( data )
		self.assertEqual( response.status_code, 200 )
		
	def test_cleaned(self):
		data = {
			"type": "cleaned", 
			"fired_at": "2009-03-26 22:01:00", 
			"data[list_id]": self.list.list_id,
			"data[campaign_id]": "4fjk2ma9xd",
			"data[reason]": "hard",
			"data[email]": "api+cleaned@mailchimp.com"
		}
		response = self._mailchimp_webhook( data )
		self.assertEqual( response.status_code, 200 )
	
	def test_upemail(self):
		data = {
			"type": "upemail", 
			"fired_at": "2009-03-26 22:15:09", 
			"data[list_id]": self.list.list_id,
			"data[new_id]": "51da8c3259", 
			"data[new_email]": "api+new@mailchimp.com", 
			"data[old_email]": "api+old@mailchimp.com"
		}
		response = self._mailchimp_webhook( data )
		self.assertEqual( response.status_code, 200 )
	
	def test_profile(self):
		# profile is not support, so we expect 404 to be raised.
		data = {
			"type": "profile", 
			"fired_at": "2009-03-26 21:31:21", 
			"data[id]": "8a25ff1d98", 
			"data[list_id]": self.list.list_id,
			"data[email]": "api@mailchimp.com", 
			"data[email_type]": "html", 
			"data[merges][EMAIL]": "api@mailchimp.com", 
			"data[merges][FNAME]": "MailChimp", 
			"data[merges][LNAME]": "API", 
			"data[merges][INTERESTS]": "Group1,Group2", 
			"data[ip_opt]": "10.20.10.30"
		}
		from django.http import Http404
		self.assertRaises( Http404, self._mailchimp_webhook, data, )




