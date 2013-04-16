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

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import select_template
from django.utils import translation
from django.views.generic import DetailView

from djangoplicity.newsletters.models import Newsletter, NewsletterType
from djangoplicity.simplearchives.views import CategoryListView


class NewsletterListView(CategoryListView):
	model = Newsletter
	model_category_field = 'type'
	category_model = NewsletterType

	def get_queryset( self ):
		# We use the parent get_category() as we need the source
		# category and not the translations
		category = super(NewsletterListView, self).get_category()
		lang = translation.get_language()

		queryset = Newsletter.objects.language(lang).filter(send__isnull=False)

		model_category_field = self.get_model_category_field()
		queryset = queryset.filter( **{ model_category_field: category } )

		self.category = self.get_category()

		return queryset

	def get_context_data( self, **kwargs ):
		context = super(NewsletterListView, self).get_context_data(**kwargs)
		context['archive_title'] = self.category.name
		# Different newsletters might have different templates (to accomodate
		# the different menus) so we check which template we should inherit from
		# by search which one is available:
		lang = translation.get_language()
		context['template_name'] = select_template([
			'newsletters/newsletter_%s_list.%s.html' % (self.category.slug, lang),
			'newsletters/newsletter_%s_list.html' % self.category.slug,
			'base.html']).name
		return context

	def get_template_names( self ):
		return ['newsletters/newsletter_list.html']


class NewsletterDetailView(DetailView):

	model = Newsletter

	def get_object(self):
		'''
		Returns the newsletter matching the pk if its type matches the slug
		'''
		slug = self.kwargs.get('category_slug')
		pk = self.kwargs.get('pk')
		newsletter_type = get_object_or_404(NewsletterType, slug=slug, archive=True)

		try:
			obj = Newsletter.objects.get(type=newsletter_type, pk=pk)
			lang = translation.get_language()
			if lang != settings.LANGUAGE_CODE:
				obj = obj.translations.get(lang=lang)
		except Newsletter.DoesNotExist:
			raise Http404

		return obj

	def get_context_data(self, **kwargs):
		'''
		Adds the NewsletterType to the context
		'''
		slug = self.kwargs.get('category_slug')
		newsletter_type = get_object_or_404(NewsletterType, slug=slug, archive=True)
		newsletter_data = self.object.render( {}, store=False )
		context = super(NewsletterDetailView, self).get_context_data(**kwargs)
		context.update({
			'newsletter_type': newsletter_type,
			'newsletter_html': newsletter_data['html'],
		})
		return context
