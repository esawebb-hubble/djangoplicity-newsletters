from datetime import datetime

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, FieldError
from django.http import Http404

from djangoplicity.archives.contrib.queries import CategoryQuery

if settings.USE_I18N:
	from djangoplicity.translation.models import TranslationModel
	from django.utils import translation


class NewsletterCategoryQuery(CategoryQuery):
	"""
	"""
	def queryset( self, model, options, request, stringparam=None, **kwargs ):

		if not stringparam:
			raise Http404

		#
		# Find category
		#
		categorymodel = self._get_categorymodel( model, self.relation_field )

		try:
			category = categorymodel.objects.get( **{ self.url_field: stringparam } )
			set_manager = getattr( category, "%s_set" % model._meta.module_name )
		except categorymodel.DoesNotExist:
			# URL of non existing category specified.
			raise Http404
		except FieldError:
			raise ImproperlyConfigured( 'URL field does not exist on category model.' )
		except AttributeError:
			raise ImproperlyConfigured( 'Related query set attribute %s_set does not exist on category model.' % model._meta.module_name )

		#if stringparam in self.featured:
		#	print "featured"

		#
		# Select archive items in category
		#
		qs = set_manager.all()

		# Filter out non-sent Newsletters
		now = datetime.now()
		qs = self._filter_datetime_by_fieldname(qs, now, 'send', False, False)

		return ( qs, { 'category': category } )
