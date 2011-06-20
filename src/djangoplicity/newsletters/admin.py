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

from django.contrib import admin
from django.utils.translation import ugettext as _
from djangoplicity.newsletters.models import Subscriber, Subscription, List, MailChimpList, MailChimpListSource, ListSynchronization

class ListSynchronizationInlinAdmin( admin.TabularInline ):
	model = ListSynchronization
	extra = 1
	fk_name = 'destination'
	
class ListSynchronizationAdmin( admin.ModelAdmin ):
	list_display = ['destination','source']
	list_filter = ['destination','source']
	
class SubscriberAdmin( admin.ModelAdmin ):
	list_display = ['email',]
	search_fields = ['email',]

class SubscriptionAdmin( admin.ModelAdmin ):
	list_display = ['subscriber','list']
	list_filter = ['list',]
	search_fields = ['subscriber__email','list__name']

class ListAdmin( admin.ModelAdmin ):
	list_display = ['name','password']
	search_fields = ['name','password']
	inlines = [ListSynchronizationInlinAdmin]
	
class MailChimpListSourceInlinAdmin( admin.TabularInline ):
	model = MailChimpListSource
	extra = 0
	
class MailChimpListAdmin( admin.ModelAdmin ):
	list_display = ['list_id', 'admin_url', 'name','default_from_name', 'default_from_email', 'email_type_option', 'member_count', 'open_rate', 'click_rate', 'connected','last_sync',]
	list_filter = ['use_awesomebar','email_type_option','last_sync','connected',]
	search_fields = ['api_key','list_id','name','web_id','default_from_name', 'default_from_email', 'email_type_option','default_subject']
	inlines = [ MailChimpListSourceInlinAdmin, ]
	fieldsets = (
		( 
			None, 
			{
				'fields' : ( 'api_key', 'list_id' ),
			}
		),
		( 
			'List information', 
			{
				'description' : 'Following information is configured in MailChimp administration interface.',
				'fields' : (
					'name',
					'web_id',
					'email_type_option',
					'use_awesomebar',
					'default_from_name',
					'default_from_email',
					'default_subject',
					'default_language',
				),
			}
		),
		( 
			'Statistics', 
			{
				'description' : 'Following information is collected by MailChimp.',
				'fields' : ( 
					'list_rating', 
					'member_count', 
					'unsubscribe_count',
					'cleaned_count',
					'member_count_since_send',
					'unsubscribe_count_since_send',
					'cleaned_count_since_send',
					'avg_sub_rate',
					'avg_unsub_rate',
					'target_sub_rate',
					'open_rate',
					'click_rate',
				),
				'classes': ( 'collapse', ),

			}
		),
		( 
			'Synchronization', 
			{
				'fields' : (
					'connected',
					'last_sync',
				),
				'classes': ( 'collapse', ),
			}
		),
	)
	
	readonly_fields = [
		'name',
		'web_id',
		'email_type_option',
		'use_awesomebar',
		'default_from_name',
		'default_from_email',
		'default_subject',
		'default_language',
		'list_rating',
		'member_count',
		'unsubscribe_count',
		'cleaned_count',
		'member_count_since_send',
		'unsubscribe_count_since_send',
		'cleaned_count_since_send',
		'avg_sub_rate',
		'avg_unsub_rate',
		'target_sub_rate',
		'open_rate',
		'click_rate',
		'connected',
		'last_sync',
	]
	
	def admin_url( self, obj ):
		url = obj.get_admin_url()
		return """<a href="%s">MailChimp</a>""" % url if url else ""
	admin_url.short_description = "Admin URL"
	admin_url.allow_tags = True
	

class MailChimpListSourceAdmin( admin.ModelAdmin ):
	list_display = ['list','mailchimplist']
	list_filter = ['list','mailchimplist']
	

def register_with_admin( admin_site ):
	admin_site.register( Subscriber, SubscriberAdmin )
	admin_site.register( Subscription, SubscriptionAdmin )
	admin_site.register( List, ListAdmin )
	admin_site.register( ListSynchronization, ListSynchronizationAdmin )
	admin_site.register( MailChimpList, MailChimpListAdmin )
	admin_site.register( MailChimpListSource, MailChimpListSourceAdmin )
	
		
# Register with default admin site	
register_with_admin( admin.site )