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
from djangoplicity.newsletters.models import NewsletterType, Newsletter, NewsletterContent, NewsletterDataSource

class NewsletterAdmin( admin.ModelAdmin ):
	list_display = ['type', 'from_name', 'from_email', 'subject','release_date','published','last_modified']
	list_editable = ['from_name', 'from_email', 'subject', ]
	list_filter = ['type', 'last_modified', 'published']
	search_fields = ['from_name', 'from_email', 'subject', 'html', 'text']
	
class NewsletterTypeAdmin( admin.ModelAdmin ):
	list_display = ['name', 'default_from_name', 'default_from_email', 'sharing', 'archive' ]
	list_editable = ['default_from_name', 'default_from_email', 'sharing', 'archive']
	list_filter = ['sharing', 'archive' ]
	search_fields = ['name', 'default_from_name', 'default_from_email', 'subject_template', 'html_template', 'text_template']

class NewsletterContentAdmin( admin.ModelAdmin ):
	list_display = ['newsletter', 'content_type', 'object_id', ]
	list_filter = ['newsletter__type__name', 'content_type' ]
	search_fields = ['newsletter__name', ]

class NewsletterDataSourceAdmin( admin.ModelAdmin ):
	list_display = ['name', 'title', 'type', 'content_type', 'list' ]
	list_editable = ['type', 'title', 'content_type', 'list' ]
	list_filter = ['list', 'type', 'content_type', ]
	search_fields = ['name', 'title' ]

def register_with_admin( admin_site ):
	admin_site.register( NewsletterType, NewsletterTypeAdmin )
	admin_site.register( Newsletter, NewsletterAdmin )
	admin_site.register( NewsletterContent, NewsletterContentAdmin )
	admin_site.register( NewsletterDataSource, NewsletterDataSourceAdmin )
		
# Register with default admin site	
register_with_admin( admin.site )