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
from djangoplicity.newsletters.models import NewsletterType, Newsletter, NewsletterContent, NewsletterDataSource, DataSourceOrdering, DataSourceSelector
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.conf.urls.defaults import patterns

class NewsletterDataSourceInlineAdmin( admin.TabularInline ):
	model = NewsletterDataSource
	extra = 0
	
class NewsletterContentInlineAdmin( admin.TabularInline ):
	model = NewsletterContent
	extra = 0

from tinymce.widgets import TinyMCE
from django.db import models

class NewsletterAdmin( admin.ModelAdmin ):
	list_display = [ 'id', 'subject', 'type', 'from_name', 'from_email', 'release_date','published','last_modified']
	list_editable = ['from_name', 'from_email', 'subject', ]
	list_filter = ['type', 'last_modified', 'published']
	search_fields = ['from_name', 'from_email', 'subject', 'html', 'text']
	readonly_fields = ['last_modified',]
	fieldsets = (
		( 
			None, 
			{
				'fields' : ( 'type', 'release_date', 'published', 'frozen', 'last_modified' ),
			}
		),
		( 
			"Auto generation", 
			{
				'fields' : ( 'start_date', 'end_date' ),
			}
		),
		( 
			"Sender", 
			{
				'fields' : ( 'from_name', 'from_email' ),
			}
		),
		( 
			"Content", 
			{
				'fields' : ( 'subject', 'editorial' ),
			}
		),
	)
	inlines = [NewsletterContentInlineAdmin]
	formfield_overrides = {
        models.TextField: {'widget': TinyMCE( attrs={'cols': 80, 'rows': 20}, )},
    }
	
	def get_urls( self ):
		urls = super( NewsletterAdmin, self ).get_urls()
		extra_urls = patterns( '',
			( r'^(?P<pk>[0-9]+)/html/$', self.admin_site.admin_view( self.html_newsletter_view ) ),
			( r'^(?P<pk>[0-9]+)/text/$', self.admin_site.admin_view( self.text_newsletter_view ) ),
		)
		return extra_urls + urls
	
	def html_newsletter_view( self, request, pk=None ):
		"""
		View HTML version of newsletter
		"""
		newsletter = get_object_or_404( Newsletter, pk=pk )
		return HttpResponse( newsletter.html, mimetype="text/html" )
	
	def text_newsletter_view( self, request, pk=None ):
		"""
		View text version of newsletter
		"""
		newsletter = get_object_or_404( Newsletter, pk=pk )
		response = HttpResponse( newsletter.text )
		response["Content-Type"] = "text/plain; charset=utf-8"
		return response
		


	

class NewsletterTypeAdmin( admin.ModelAdmin ):
	list_display = ['name', 'default_from_name', 'default_from_email', 'sharing', 'archive' ]
	list_editable = ['default_from_name', 'default_from_email', 'sharing', 'archive']
	list_filter = ['sharing', 'archive' ]
	search_fields = ['name', 'default_from_name', 'default_from_email', 'subject_template', 'html_template', 'text_template']
	inlines = [NewsletterDataSourceInlineAdmin]

class NewsletterContentAdmin( admin.ModelAdmin ):
	list_display = ['newsletter', 'content_type', 'object_id', ]
	list_filter = ['newsletter__type__name', 'content_type' ]
	search_fields = ['newsletter__name', ]

class NewsletterDataSourceAdmin( admin.ModelAdmin ):
	list_display = ['name', 'title', 'type', 'content_type', 'list' ]
	list_editable = ['type', 'title', 'content_type', 'list' ]
	list_filter = ['list', 'type', 'content_type', ]
	search_fields = ['name', 'title' ]
	
class DataSourceSelectorAdmin( admin.ModelAdmin ):
	list_display = [ 'id', 'name', 'filter', 'field', 'match', 'value' ]
	list_editable = ['name', 'filter', 'field', 'match', 'value' ]
	list_filter = [ 'filter', 'match' ]
	search_fields = [ 'name', 'filter', 'field', 'match', 'value' ]
	
class DataSourceOrderingAdmin( admin.ModelAdmin ):
	list_display = [ 'id', 'name', 'fields', ]
	list_editable = ['name', 'fields', ]
	list_filter = []
	search_fields = [ 'name', 'fields', ]

def register_with_admin( admin_site ):
	admin_site.register( NewsletterType, NewsletterTypeAdmin )
	admin_site.register( Newsletter, NewsletterAdmin )
	admin_site.register( DataSourceOrdering, DataSourceOrderingAdmin )
	admin_site.register( DataSourceSelector, DataSourceSelectorAdmin )
	#admin_site.register( NewsletterContent, NewsletterContentAdmin )
	#admin_site.register( NewsletterDataSource, NewsletterDataSourceAdmin )
		
# Register with default admin site	
register_with_admin( admin.site )