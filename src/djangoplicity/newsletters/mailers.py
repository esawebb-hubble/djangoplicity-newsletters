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

from django.core.mail import EmailMultiAlternatives

class MailerPlugin():
	"""
	Interface for mailer implementations
	"""
	name = ''
	parameters = []
	
	def __init__( self, params ):
		pass
	
	def send_now( self, newsletter ):
		raise NotImplementedError
	
	def send_test( self, newsletter, emails ):
		raise NotImplementedError
	
	def schedule( self, newsletter, delivery ):
		raise NotImplementedError
	
	@classmethod
	def get_class_path( cls ):
		return "%s.%s" % ( cls.__module__, cls.__name__ )


class EmailMailerPlugin( MailerPlugin ):
	"""
	Mailer implementation that will send the newsletter to a predefined
	list of email addresses (which could be e.g. a mailing list). 
	"""
	name = 'Standard mailer'
	parameters = [ ( 'emails', 'Comma separated list of emails to send to.', 'str' ) ]

	def __init__( self, params ):
		try:
			self._to_emails = [x.strip() for x in params['emails'].split()]
		except KeyError:
			raise Exception( "Parameter 'emails' is missing" )

	def _send( self, newsletter, emails ):
		"""
		Send combined html and plain text email.
		"""
		from_email = '%s <%s>' % ( newsletter.from_name, newsletter.from_email )
		msg = EmailMultiAlternatives( newsletter.subject, newsletter.text, from_email, emails )
		msg.attach_alternative( newsletter.html, "text/html" )
		msg.send()

	def send_now( self, newsletter ):
		self._send( newsletter, self._to_emails )

	def send_test( self, newsletter, emails ):
		self._send( newsletter, emails )