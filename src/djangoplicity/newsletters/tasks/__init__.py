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
The celery tasks defined here are all wrapping features defined in the models.
"""

from celery.task import task


@task( name="newsletters.send_scheduled_newsletter", ignore_result=True )
def send_scheduled_newsletter( newsletter_pk ):
	"""
	Task to start sending a scheduled newsletter - this task should normally
	be invoked with the eta keyword argument (e.g apply_async( pk, eta=.. ))

	The task will be revoked if the schedule is cancelled via the admin
	interface.

	Notes:
	- A task with eta/countdown will survive if workers are restarted.
	- The eta/countdown argument only ensures that the task will be
		run after the defined time. If workers are overloaded it might be
		delayed.
	"""
	from djangoplicity.newsletters.models import Newsletter

	logger = send_scheduled_newsletter.get_logger()

	nl = Newsletter.objects.get( pk=newsletter_pk )

	logger.info("Starting to send scheduled newsletter %s" % newsletter_pk)

	nl._send()


@task( name="newsletters.send_newsletter", ignore_result=True )
def send_newsletter( newsletter_pk ):
	"""
	Task to start sending a newsletter
	"""
	from djangoplicity.newsletters.models import Newsletter

	logger = send_newsletter.get_logger()

	nl = Newsletter.objects.get( pk=newsletter_pk )

	logger.info("Starting to send newsletter %s" % newsletter_pk)

	nl._send_now()


@task( name="newsletters.send_newsletter_test", ignore_result=True )
def send_newsletter_test( newsletter_pk, emails ):
	"""
	Task to start sending a newsletter
	"""
	from djangoplicity.newsletters.models import Newsletter

	logger = send_newsletter.get_logger()

	nl = Newsletter.objects.get( pk=newsletter_pk )

	logger.info( "Starting to send test newsletter %s" % newsletter_pk )

	nl._send_test( emails )


@task( name="newsletters.schedule_newsletter", ignore_result=True )
def schedule_newsletter( newsletter_pk ):
	"""
	Task to schedule a newsletter for delivery.
	"""
	from djangoplicity.newsletters.models import Newsletter

	logger = schedule_newsletter.get_logger()

	nl = Newsletter.objects.get( pk=newsletter_pk )

	logger.info("Scheduling newsletter %s" % newsletter_pk)

	nl._schedule()


@task( name="newsletters.unschedule_newsletter", ignore_result=True )
def unschedule_newsletter( newsletter_pk ):
	"""
	Task to unschedule a newsletter for delivery.
	"""
	from djangoplicity.newsletters.models import Newsletter

	logger = unschedule_newsletter.get_logger()

	nl = Newsletter.objects.get( pk=newsletter_pk )

	logger.info("Unscheduling newsletter %s" % newsletter_pk)

	nl._unschedule()


@task( name="newsletters.abuse_reports", ignore_result=True )
def abuse_reports():
	"""
	Generate a report for abuse reports for campaigns sent
	over the last 4 weeks.
	This task is meant to be run once a week
	"""
	from datetime import datetime, timedelta
	from django.core.mail import EmailMessage
	from djangoplicity.mailinglists.models import MailChimpList
	from djangoplicity.newsletters.models import MailChimpMailerPlugin
	from django.contrib.sites.models import Site

	logger = abuse_reports.get_logger()

	email_from = 'no-reply@eso.org'
	email_reply_to = 'mandre@eso.org'
	email_to = ['osandu@partner.eso.org', 'mandre@eso.org', 'lars@eso.org']

	#  Calculate the date 4 weeks ago
	start_date = datetime.today() - timedelta(weeks=4)
	#  Calculate the date one week ago
	week_ago = datetime.today() - timedelta(weeks=1)

	body = ''
	n_complaints = 0

	for ml in MailChimpList.objects.all():
		#  Fetch the list of campaigns sent within the last 4 weeks
		campaigns = ml.connection.campaigns.list(filters={'list_id': ml.list_id, 'sendtime_start': start_date.strftime('%Y-%m-%d %H:%M:%S')},
											limit=1000)
		if campaigns['total'] == 0:
			continue

		content = ''

		for campaign in campaigns['data']:
			complaints = ml.connection.reports.abuse(cid=campaign['id'], opts={'since': week_ago.strftime('%Y-%m-%d %H:%M:%S')})
			if complaints['total'] == 0:
				continue
			else:
				n_complaints += complaints['total']

			if not content:
				name = 'MailChimp List: %s' % ml.name
				content = '=' * len(name) + '\n'
				content += name + '\n'
				content += '=' * len(name) + '\n'

			title = 'Campaign: %s (%d complaints)' % (campaign['title'], complaints['total'])
			content += '\n' + title + '\n'
			content += '-' * len(title) + '\n'
			for complaint in complaints['data']:
				member = ml.connection.lists.member_info(id=ml.list_id, emails=[{'email': complaint['member']['email']}])
				if 'code' in member:
					logger.critical('Error running listMemberInfo: "%s"' % member['error'])
					continue
				if member['success_count'] != 1:
					logger.critical('Can\'t identify member "%s"' % complaint['member']['email'])
					continue

				content += '%s https://us2.admin.mailchimp.com/lists/members/view?id=%s' % (complaint['member']['email'], member['data'][0]['web_id']) + '\n'

		body += content

	if body:
		logger.info('Sending report for %d complaints' % n_complaints)
		# Prepare the message:
		msg = EmailMessage()
		msg.headers = {'Reply-To': email_reply_to}
		msg.subject = '%d complaints reported in MailChimp for %s' % (n_complaints, Site.objects.get_current().domain)
		msg.from_email = email_from
		msg.to = email_to
		msg.body = body

		msg.send()
	else:
		logger.info('No Mailchimp Complaints found')
