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
if settings.USE_I18N:
	from django.utils import translation
from django.views.generic import DetailView

from djangoplicity.newsletters.models import Newsletter, NewsletterType


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

			if not obj.published and not (self.request.user.is_superuser or self.request.user.is_staff):
				raise Http404

			if settings.USE_I18N:
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
		# If the archive is restricted to internal access only we return a 404
		# if the client is outside the internal network
		if newsletter_type.internal_archive:
			if not (self.request and "REMOTE_ADDR" in self.request.META and self.request.META["REMOTE_ADDR"] in settings.INTERNAL_IPS):
				raise Http404
		return context
