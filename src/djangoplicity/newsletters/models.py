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

"""
The newsletter system consists of the following components:

	* Newsletter types which are used to define:
	* where to send the newsletter
	* how to render the newsletter
	* how to select content for the newsletter (auto-generation support)
	* Mailer plug-in system that allow sending a newsletter
		via different channels (e.g. via mailchimp, standard email or mailman list).
		The mailer plug-in system can be extended with the users own mailer plug-ins.
	* Newsletter generation component, that can integrate content from any django
		model into the newsletter.

----
"""

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import post_save
from django.template import Context, Template, defaultfilters
from django.utils.translation import ugettext as _
from django.utils import translation
from djangoplicity import archives
from djangoplicity.archives.contrib import types
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.newsletters.mailers import EmailMailerPlugin, MailerPlugin, \
	MailmanMailerPlugin
from djangoplicity.newsletters.tasks import send_newsletter, \
	send_newsletter_test, schedule_newsletter, unschedule_newsletter, \
	send_scheduled_newsletter
from djangoplicity.translation.models import TranslationModel, translation_permalink
from djangoplicity.utils.templatetags.djangoplicity_text_utils import unescape
import logging
import traceback
from django.utils import translation

logger = logging.getLogger(__name__)


def make_nl_id():
	'''
	Create a new Unique ID for the newsletter based on the largest
	existing ID so far
	'''
	max_id = 0
	for id in Newsletter.objects.values_list('id', flat=True):
		try:
			id = int(id)
		except ValueError:
			# We're only intersted in string integers, skip!
			continue
		if id > max_id:
			max_id = id

	return str(max_id + 1)


class Mailer( models.Model ):
	"""
	Model for defining mailers. A newsletter type can define several mailers to use
	when sending a newsletter (e.g. send newsletter via mailchimp and two other mail-man
	mailing lists). Each mailer defines the plug-in to use parameters for each plugin.
	"""
	_plugins = {}

	plugin = models.CharField( max_length=255, blank=False, choices=[] )
	name = models.CharField( max_length=255 )

	def __init__( self, *args, **kwargs ):
		"""
		Set choices for plugin field dynamically based on registered plugins.
		"""
		super( Mailer, self ).__init__( *args, **kwargs )
		self._meta.get_field_by_name( 'plugin' )[0]._choices = Mailer.get_plugin_choices()  # lazy( Mailer.get_plugin_choices, list )

	def get_plugincls( self ):
		"""
		Get the mailer plug-in class for this mailer.
		"""
		try:
			return self._plugins[ self.plugin ]
		except KeyError:
			raise Exception( "Plug-in %s does not exists." % self.plugin )

	def get_plugin( self ):
		"""
		Get an instance of the plug-in for this mailer
		"""
		cls = self.get_plugincls()
		return cls( self.get_parameters() )

	def get_parameters( self ):
		"""
		Get parameters to be send to the mailer
		"""
		return dict( [( p.name, p.get_value() ) for p in MailerParameter.objects.filter( mailer=self ) ] )

	def on_scheduled( self, newsletter ):
		"""
		Notification that the given newsletter was scheduled for sending
		"""
		plugin = self.get_plugin()
		return plugin.on_scheduled( newsletter )

	def on_unscheduled( self, newsletter ):
		"""
		Notification that the scheduled newsletter was
		cancelled.
		"""
		plugin = self.get_plugin()
		return plugin.on_unscheduled( newsletter )

	def send_now( self, newsletter ):
		"""
		Send newsletter now via this mailer
		"""
		l = self._log_entry( newsletter )

		try:
			plugin = self.get_plugin()
			return plugin.send_now( newsletter )
		except Exception, dummy_e:
			l.succeess = False
			l.error = traceback.format_exc()
		finally:
			l.save()

	def send_test( self, newsletter, emails=[] ):
		"""
		Send test newsletter now via this mailer to listed emails
		"""
		l = self._log_entry( newsletter )
		l.is_test = True

		try:
			plugin = self.get_plugin()
			res = plugin.send_test( newsletter, emails )
			l.save()
			return res
		except:
			l.success = False
			l.error = traceback.format_exc()
			l.save()

	def _log_entry( self, newsletter ):
		"""
		Create a log entry for sending a mail
		"""
		l = MailerLog(
				plugin=self.plugin,
				name=self.name,
				subject=newsletter.subject,
				newsletter_pk=newsletter.pk,
				parameters='; '.join([unicode( p ) for p in MailerParameter.objects.filter( mailer=self )]),
			)
		return l

	@classmethod
	def register_plugin( cls, mailercls ):
		"""
		Register a new mailer plug-in.
		"""
		if issubclass( mailercls, MailerPlugin ):
			cls._plugins[mailercls.get_class_path()] = mailercls

	@classmethod
	def get_plugin_choices( cls ):
		"""
		Get list of mailer plug-in choices
		"""
		choices = [ ( p, pcls.name ) for p, pcls in cls._plugins.items() ]
		choices.sort( key=lambda x: x[1] )
		return list( choices )

	@classmethod
	def post_save_handler( cls, sender=None, instance=None, created=False, raw=True, using=None, **kwargs ):
		"""
		Callback to save a blank value for all parameters for this plugin and remove unknown parameters
		"""
		if instance and not raw:
			known_params = dict( [( p.name, p ) for p in MailerParameter.objects.filter( mailer=instance )] )

			for p, desc, t in instance.get_plugincls().parameters:
				touched = False
				try:
					param = MailerParameter.objects.get( mailer=instance, name=p )
				except MailerParameter.DoesNotExist:
					param = MailerParameter( mailer=instance, name=p )
					touched = True

				for attr, val in [( 'type', t ), ( 'help_text', desc )]:
					if getattr( param, attr ) != val:
						setattr( param, attr, val )
						touched = True

				if touched:
					param.save()

				try:
					del known_params[ param.name ]
				except KeyError:
					pass

			# Delete unknown parameters
			for param in known_params.values():
				param.delete()

	def __unicode__( self ):
		return "%s: %s" % ( self.get_plugincls().name, self.name )

	class Meta:
		ordering = ['name']

# Connect signal handlers
post_save.connect( Mailer.post_save_handler, sender=Mailer )


class MailerParameter( models.Model ):
	"""
	Parameter for a mailer (e.g. mailchimp list id, or list of email addresses).

	The mail parameters are automatically created by
	"""
	mailer = models.ForeignKey( Mailer )
	name = models.SlugField( max_length=255, unique=False )
	value = models.CharField( max_length=255, blank=True, default='' )
	type = models.CharField( max_length=4, default='str', choices=[ ( 'str', 'Text' ), ( 'int', 'Integer' ), ( 'bool', 'Boolean' ), ( 'date', 'Date' ), ] )
	help_text = models.CharField( max_length=255, blank=True )

	def get_value( self ):
		"""
		Return value in the proper type
		"""
		if self.type == 'str':
			return self.value
		elif self.type == 'int':
			try:
				return int( self.value )
			except ValueError:
				return None
		elif self.type == 'bool':
			return ( self.value ).lower() == 'true'
		elif self.type == 'date':
			return self.value

	def __unicode__( self ):
		return u"%s = %s (%s)" % ( self.name, self.value, self.type )

	class Meta:
		ordering = ['mailer', 'name']
		unique_together = ['mailer', 'name']


class MailerLog( models.Model ):
	"""
	"""
	timestamp = models.DateTimeField( auto_now_add=True )
	success = models.BooleanField( default=True )
	is_test = models.BooleanField( default=False )
	plugin = models.CharField( max_length=255 )
	name = models.CharField( max_length=255 )
	parameters = models.TextField( blank=True )
	subject = models.CharField( max_length=255, blank=False )
	newsletter_pk = models.IntegerField()
	error = models.TextField( blank=True )

	class Meta:
		ordering = ['-timestamp']


class Language( models.Model ):
	"""
	Available languages for Local newsletters
	"""
	lang = models.CharField(primary_key=True, verbose_name=_( 'Language' ), max_length=5, choices=settings.LANGUAGES)

	def __unicode__( self ):
		for lang, name in settings.LANGUAGES:
			if lang == self.lang:
				return name
		return 'Unknown language in settings; "%s"' % self.lang

	class Meta:
		ordering = ['lang']


class NewsletterType( models.Model ):
	"""
	Definition of a newsletter type - e.g. ESO Outreach Community Newsletter
	"""
	#
	# Default from email/name
	#
	name = models.CharField( max_length=255 )
	slug = models.SlugField(help_text=_('Slug for e.g. online archive URL'))
	default_from_name = models.CharField( max_length=255 )
	default_from_email = models.EmailField()

	#
	# Templates for subject, text, and html
	#
	subject_template = models.CharField( max_length=255, blank=True )
	text_template = models.TextField( blank=True )
	html_template = models.TextField( blank=True, verbose_name="HTML template" )

	#
	# Options fields
	#
	archive = models.BooleanField( default=True, help_text=_( 'Enable public archives for this newsletter type.' ) )
	local_archive = models.BooleanField( default=False, help_text=_( 'Use local archive (instead of e.g. Mailchimp Online archive)' ) )
	internal_archive = models.BooleanField( default=False, help_text=_( 'Restrict archive to internal network only.' ) )
	sharing = models.BooleanField( default=True, help_text=_( 'Enable social sharing of newsletter.' ) )

	subscribe_text = models.TextField(blank=True, help_text=_('Instructions and link to subscribe to the newsletter'))

	#
	# Mailers
	#
	mailers = models.ManyToManyField( Mailer, blank=True )

	#
	# Languages
	#
	languages = models.ManyToManyField( Language, blank=True, through='NewsletterLanguage' )

	def get_generator( self ):
		return NewsletterGenerator( type=self )

	@translation_permalink
	def get_absolute_url( self ):
		lang = translation.get_language()
		return ( lang, 'newsletters_defaultquery', [self.slug, ] )

	def __unicode__( self ):
		return self.name

	class Meta:
		ordering = ['name']


class NewsletterLanguage( models.Model ):
	"""
	Available languages for Local newsletters
	"""
	newsletter_type = models.ForeignKey(NewsletterType)
	language = models.ForeignKey(Language)
	default_from_name = models.CharField( max_length=255, blank=True, null=True )
	default_from_email = models.EmailField( blank=True, null=True)
	default_editorial = models.TextField( blank=True )
	default_editorial_text = models.TextField( blank=True )

	def __unicode__( self ):
		return '%s - %s' % (self.newsletter_type, self.language.lang)

	class Meta:
		ordering = ['language']


class Newsletter( archives.ArchiveModel, TranslationModel ):
	"""
	A definition of a newsletter.
	"""

	SCHEDULED_CHOICES = (
		('OFF', 'Not Scheduled'),
		('ONGOING', 'Being Scheduled'),
		('ON', 'Scheduled')
	)

	id = models.SlugField( primary_key=True )

	# Status
	type = models.ForeignKey( NewsletterType )
	frozen = models.BooleanField( default=False )
	scheduled_status = models.CharField( max_length=10, default='OFF', choices=SCHEDULED_CHOICES )
	scheduled_task_id = models.CharField( max_length=64, blank=True )
	send = models.DateTimeField( verbose_name='Sent', blank=True, null=True )

	# Auto generation support
	start_date = models.DateTimeField( blank=True, null=True )
	end_date = models.DateTimeField( blank=True, null=True )

	# From name/email
	from_name = models.CharField( max_length=255, blank=True )
	from_email = models.EmailField( blank=True )

	# Content
	subject = models.CharField( max_length=255, blank=True )
	text = models.TextField( blank=True )
	html = models.TextField( verbose_name="HTML", blank=True )

	# Editorial if needed
	editorial_subject = models.CharField( max_length=255, blank=True )
	editorial = models.TextField( blank=True )
	editorial_text = models.TextField( blank=True )

	def _schedule( self ):
		"""
		"""
		if self.scheduled_status in ('ON', 'ONGOING'):
			raise Exception("Newsletter is scheduled for sending.")
		elif self.send:
			raise Exception("Newsletter has already been sent.")
		else:
			if datetime.now() + timedelta( minutes=2 ) >= self.release_date:
				raise Exception("Cannot schedule newsletter to be sent in the past.")

			self.scheduled_status = 'ONGOING'
			self.save()

			try:
				for m in self.type.mailers.all():
					m.on_scheduled( self )
			except Exception, e:
				# Something wrong happen, set scheduled_status to 'OFF
				# and re-raise the exception
				self.scheduled_status = 'OFF'
				self.save()
				raise e

			res = send_scheduled_newsletter.apply_async( args=[ self.pk ], eta=self.release_date )

			self.scheduled_task_id = res.task_id
			self.scheduled_status = 'ON'
			self.save()

	def _unschedule( self ):
		"""
		"""
		if self.send:
			raise Exception("Newsletter has already been sent")
		elif self.scheduled_status == 'OFF':
			raise Exception("Newsletter is not scheduled for sending.")
		else:
			from celery.task.control import revoke

			if not self.scheduled_task_id:
				raise Exception("Scheduled task ID does not exist. Cannot cancel sending.")

			revoke( self.scheduled_task_id )

			for m in self.type.mailers.all():
				m.on_unscheduled( self )

			self.scheduled_status = 'OFF'
			self.scheduled_task_id = ""
			self.save()

	def _send_now( self ):
		"""
		Function that does the actual work. Is called from
		the task send_newsletter
		"""
		if self.scheduled_status == 'OFF':
			self._send()
		else:
			raise Exception( "Newsletter is scheduled for sending. To send now, you must first cancel the current schedule." )

	def _send( self ):
		"""
		Send newsletter
		"""
		if self.send is None:
			self.send = datetime.now()
			if self.type.archive:
				self.published = True

			if self.scheduled_status != 'ON':
				raise Exception( 'Won\'t send Newsletter: Scheduling status is "%s"' % self.scheduled_status)

			for m in self.type.mailers.all():
				logger.info('Starting sending with mailer "%s"', m)
				res = m.send_now( self )
				if res:
					raise Exception(res)

			self.frozen = True
			self.save()
		else:
			raise Exception("Newsletter has already been sent.")

	def _send_test( self, emails ):
		"""
		Function that does the actual work. Is called from
		the task send_newsletter_test
		"""
		for m in self.type.mailers.all():
			res = m.send_test( self, emails )
			if res:
				raise Exception(res)

	def schedule( self ):
		"""
		Schedule a newsletter for sending.
		"""
		if not self.send and self.scheduled_status == 'OFF':
			schedule_newsletter.delay( self.pk )

	def unschedule( self ):
		"""
		Cancel current schedule for newsletter
		"""
		if self.scheduled_status == 'ON':
			unschedule_newsletter.delay( self.pk )

	def send_now( self ):
		"""
		Send a newsletter right away. Once send, it
		cannot be send again.

		Note each mailer will render the newsletter, since subscription
		links etc might change depending on the mailer.
		"""
		if not self.send and self.scheduled_status == 'OFF':
			send_newsletter.delay( self.pk )

	def send_test( self, emails ):
		"""
		Send a test version of the newsletter.

		Note each mailer will render the newsletter, since subscription
		links etc might change depending on the mailer.
		"""

		send_newsletter_test.delay( self.pk, emails )

	@classmethod
	def latest_for_type( cls, type ):
		"""
		Get the latest published newsletter issue for a specific type.
		"""
		qs = cls.objects.filter( type=type, published=True ).order_by( '-release_date' )
		if len( qs ) > 0:
			return qs[0]
		else:
			return None

	def render( self, extra_ctx, store=True ):
		"""
		Render the newsletter
		"""
		if self.is_source() and self.frozen or \
			self.is_translation() and self.source.frozen:
			return {
				'html': self.html,
				'text': self.text,
				'subject': self.subject,
			}

		t_html = Template( self.type.html_template )
		t_text = Template( self.type.text_template )
		t_subject = Template( self.type.subject_template ) if self.type.subject_template else None

		# Flag to check if we have a custom editorial
		custom_editorial = False
		if self.is_translation():
			try:
				language = NewsletterLanguage.objects.get(language__lang=self.lang, newsletter_type=self.source.type)
				if self.editorial != language.default_editorial:
					custom_editorial = True
			except NewsletterLanguage.DoesNotExist:
				# This happens if we're accessing a NL for a language which
				# is no longer configured so we can just ignore it
				pass

		defaults = {
			'base_url': "http://%s" % Site.objects.get_current().domain,
			'MEDIA_URL': settings.MEDIA_URL,
			'STATIC_URL': settings.STATIC_URL,
			'ARCHIVE_ROOT': getattr( settings, "ARCHIVE_ROOT", "" ),
			'newsletter': self,
			'newsletter_type': self.type,
			'language': self.lang,
			'data': NewsletterContent.data_context( self, lang=self.lang ),
			'editorial_subject': self.editorial_subject,
			'editorial': self.editorial,
			'editorial_text': self.editorial_text,
			'custom_editorial': custom_editorial,
			'enable_sharing': self.type.sharing,
			'enable_archive': self.type.archive,
			'use_local_archive': self.type.local_archive,
			'release_date': self.release_date,
			'published': self.published,
			'unsubscribe_link': '',  # Will be provided by the mailer plugin
			'preferences_link': '',  # Will be provided by the mailer plugin
			'browser_link': '',  # Will be provided by the mailer plugin
			'now': datetime.now(),
			'newsletter_id': self.id,
		}
		defaults.update( extra_ctx )
		ctx = Context( defaults )

		translation.activate(self.lang)

		data = {
			'html': t_html.render( ctx ),
			'text': t_text.render( ctx ),
			'subject': t_subject.render( ctx ) if t_subject else self.subject,
		}
		translation.deactivate()

		if store:
			self.html = data['html']
			self.text = data['text']
			self.subject = data['subject']

		return data

	def save( self, *args, **kwargs ):
		if not self.pk:
			self.pk = make_nl_id()

		if not self.created:
			self.created = datetime.today()

		if self.is_source() and not self.frozen:
			if self.from_name == '':
				self.from_name = self.type.default_from_name
			if self.from_email == '':
				self.from_email = self.type.default_from_email
			if self.editorial_text == '' and self.editorial:
				self.editorial_text = defaultfilters.striptags( unescape( defaultfilters.safe( self.editorial ) ) )

			self.render( {} )

			for local in self.translations.all():
				local.render( {} )
				local.save()

		elif self.is_translation():
			try:
				language = NewsletterLanguage.objects.get(language__lang=self.lang, newsletter_type=self.source.type)
				if self.from_name == '' and language.default_from_name:
					self.from_name = language.default_from_name
				if self.from_email == '' and language.default_from_email:
					self.from_email = language.default_from_email

				if self.editorial == '' and language.default_editorial:
					self.editorial = language.default_editorial
				if self.editorial_text == '' and language.default_editorial_text:
					self.editorial_text = language.default_editorial_text

				if self.editorial_text == '' and self.editorial:
					self.editorial_text = defaultfilters.striptags( unescape( defaultfilters.safe( self.editorial ) ) )
			except NewsletterLanguage.DoesNotExist:
				# This should only happen if we try to save a NL for which the
				# NewsletterLanguage doesn't exist any longer
				pass

		result = super( Newsletter, self ).save()
		return result

	def view_html(self):
		if self.id:
			#  FIXME: replace by view_link() or similar
			return '<a href="/public/djangoplicity/admin/newsletters/newsletterproxy/%s/html">View HTML</a>' % str(self.id)
		else:
			return "Not present"
	view_html.allow_tags = True

	def view_text(self):
		if self.id:
			#  FIXME: replace by view_link() or similar
			return '<a href="/public/djangoplicity/admin/newsletters/newsletterproxy/%s/text">View text</a>' % str(self.id)
		else:
			return "Not present"
	view_text.allow_tags = True

	def edit(self):
		if self.id:
			#  FIXME: replace by view_link() or similar
			return '<a href="/public/djangoplicity/admin/newsletters/newsletterproxy/%s">Edit</a>' % str(self.id)
		else:
			return "Not present"
	edit.allow_tags = True

	@translation_permalink
	def get_absolute_url( self ):
		return ( self.lang, 'newsletters_detail_html', [self.type.slug, self.id if self.is_source() else self.source.id ] )

	def get_local_version( self, language ):
		"""
		Return local version of the newsletter matching language
		or None
		"""
		try:
			return self.translations.get( lang=language )
		except Newsletter.DoesNotExist:
			return None

	def __unicode__( self ):
		return self.subject

	class Meta:
		ordering = ['-release_date']

	class Archive:
		original = archives.ImageResourceManager(type=types.OriginalImageType)
		screen = archives.ImageResourceManager(derived='original', type=types.ScreensizeJpegType)
		news = archives.ImageResourceManager(derived='original', type=types.NewsJpegType)
		newsmini = archives.ImageResourceManager(derived='news', type=types.NewsMiniJpegType)
		newsfeature = archives.ImageResourceManager(derived='news', type=types.JpegType)
		medium = archives.ImageResourceManager(derived='original', type=types.MediumJpegType)
		mini = archives.ImageResourceManager(derived='original', type=types.MiniJpegType)
		frontpagethumbs = archives.ImageResourceManager(derived='original', type=types.FrontpageThumbnailJpegType)
		thumbs = archives.ImageResourceManager(derived='original', type=types.ThumbnailJpegType)

		class Meta:
			root = ''
			release_date = True
			embargo_date = False
			last_modified = True
			created = True
			published = True
			root = settings.NEWSLETTERS_ARCHIVE_ROOT
			# rename_pk = ('internal_internalimage', 'id')
			# rename_fks = (
							# ('internal_internalimage', 'source_id'),
							# ('internal_internalimagecontact', 'image_id'),
						# )

	class Translation:
		fields = ['subject', 'editorial', 'editorial_text', ]
		excludes = ['html', 'text', 'from_name', 'from_email']

# ========================================================================
# Translation proxy model
# ========================================================================


class NewsletterProxy( Newsletter, TranslationProxyMixin ):
	"""
	Image proxy model for creating admin to edit
	translated objects.
	"""
	objects = Newsletter.translation_objects

	def clean( self ):
		# Note: For some reason it's not possible to
		# to define clean/validate_unique in TranslationProxyMixin
		# so we have to do this trick, where we add the methods and
		# call into translation proxy micin.
		self.id_clean()

	def validate_unique( self, exclude=None ):
		self.id_validate_unique( exclude=exclude )

	class Meta:
		proxy = True
		verbose_name = _('Newsletter translation')
		app_label = 'newsletters'
		ordering = ['lang']

	class Archive:
		class Meta:
#            rename_pk = ('media_image','id')
			rename_fks = []


class NewsletterContent( models.Model ):
	"""
	Specifies content for a specific newsletter. Note, that
	only content objects of allowed content types will be
	available in the templates.
	"""
	newsletter = models.ForeignKey( Newsletter )
	data_source = models.ForeignKey( 'NewsletterDataSource', null=True, blank=True )
	object_id = models.SlugField()

	class Meta:
		ordering = ['newsletter', 'data_source', 'object_id', ]

	@classmethod
	def data_context( cls, newsletter, lang=None ):
		"""
		Generate a data context for a newsletter
		"""
		ctx = {}

		# If newsletter is a translation we use the data
		# NewsletterContent from the source Newsletter
		if newsletter.is_translation():
			newsletter = newsletter.source

		for datasrc in NewsletterDataSource.data_sources( newsletter.type ):
			# For each data source - get object(s) for this newsletter.
			modelcls = datasrc.content_type.model_class()
			data = None

			if modelcls is not None:
				content_objects = cls.objects.filter( newsletter=newsletter, data_source=datasrc )
				allpks = [obj.object_id for obj in content_objects]

				try:
					if datasrc.list:
						data = modelcls.objects.filter( pk__in=allpks )
						if datasrc.ordering:
							data = data.order_by( *datasrc.ordering.get_order_by() )
					else:
						if len( allpks ) > 0:
							data = modelcls.objects.get( pk=allpks[0] )
				except modelcls.DoesNotExist:
					data = None

			# Data can be either a list or a unique element
			# so we turn it in a list:
			if not datasrc.list:
				data = [data, ]

			#  Some 'source' content is in a given language,
			#  we skip those unless they match the passed language
			tmpdata = []
			for d in data:
				# Check if the data has a language:
				if hasattr(d, 'lang'):
					if d.lang == lang or d.lang == settings.LANGUAGE_CODE:
						# data language matches current language or default language
						tmpdata.append(d)
				else:
					# TODO:
					# We only display exhibitions, ongoing_events and special_events
					# if their country matches the current language (or if they don't
					# have a country.
					# If the newsletter language is the default system one (usually 'en')
					# we show all datasources
					# Ideally this shouldn't be hard coded here... It should be
					# possible to add a sepcial flag in the 'Newsletter data
					# sources' of the NewsletterType
					if datasrc.name in ('exhibitions', 'ongoing_events', 'special_events'):
						country = lang
						# Extract the country from the language code if necessary
						# e.g.: at for de-at
						if '-' in country:
							country = country.split('-')[1]
						if lang == settings.LANGUAGE_CODE or \
							not d.country or \
								(d.country and d.country.isocode == country):
							tmpdata.append(d)
					else:
						tmpdata.append(d)

			# If a language is passed, fetch the translations (if any)
			if not lang:
				if datasrc.list:
					data = tmpdata
				else:
					data = tmpdata.pop()
			else:
				data = []
				for d in tmpdata:
					try:
						if hasattr(d, 'get_translations'):
							d = d.get_translations()['translations'][lang]
					except KeyError:
						# No translation available, use original
						pass
					if datasrc.list:
						data.append(d)
					else:
						data = d
			ctx[datasrc.name] = data

		return ctx


class DataSourceSelector( models.Model ):
	"""
	Data source selector is used for selecting objects when auto-generating
	newsletters.
	"""
	name = models.CharField( max_length=255 )
	filter = models.CharField( max_length=1, default='I', choices=[( 'I', "Include" ), ( 'E', "Exclude" )] )
	field = models.SlugField()
	match = models.SlugField()
	value = models.CharField( max_length=255 )
	type = models.CharField( max_length=4, default='str', choices=[ ( 'str', 'Text' ), ( 'int', 'Integer' ), ( 'bool', 'Boolean' ), ( 'date', 'Date' ), ] )

	def get_query_dict( self, ctx ):
		"""
		Get a dictionary to use in a query object for this selector.
		"""
		return { str( "%s__%s" % ( self.field, self.match ) ): self.get_value( ctx )  }

	def get_value( self, ctx={} ):
		"""
		Get value to search for. Context is passed in from the newsletter generator.
		"""
		if self.type == 'str':
			return self.value % ctx
		elif self.type == 'int':
			try:
				return int( self.value % ctx )
			except ValueError:
				return None
		elif self.type == 'bool':
			return ( self.value % ctx ).lower() == 'true'
		elif self.type == 'date':
			return self.value % ctx

	def get_q_object( self, ctx ):
		"""
		Get query object for this queryset selector
		"""
		d = self.get_query_dict( ctx )

		return models.Q( **d ) if self.filter == 'I' else ~models.Q( **d )

	def __unicode__( self ):
		return self.name

	class Meta:
		ordering = ['name']


class DataSourceOrdering( models.Model ):
	"""
	Data source ordering is used to order objects in a data source
	when auto-generating objects
	"""
	name = models.CharField( max_length=255 )
	fields = models.SlugField()

	def get_order_by( self ):
		return [x.strip() for x in self.fields.split( ',' ) ]

	def __unicode__( self ):
		return self.name

	class Meta:
		ordering = ['name']


class NewsletterDataSource( models.Model ):
	"""
	Data source for a newsletter. A data source is a reference to a
	django content type combined with selectors, ordering etc. that
	can be used to generate a normal query set for selecting new
	objects
	"""
	type = models.ForeignKey( NewsletterType )
	list = models.BooleanField( default=True )
	name = models.SlugField( help_text=_( 'Name used to access this data source in templates' ) )
	title = models.CharField( max_length=255 )
	content_type = models.ForeignKey( ContentType )
	selectors = models.ManyToManyField( DataSourceSelector, blank=True )
	ordering = models.ForeignKey( DataSourceOrdering, null=True, blank=True )
	limit = models.CharField( max_length=255, blank=True )

	def __unicode__( self ):
		return "%s: %s" % ( self.type, self.title )

	def _limit_queryset( self, qs ):
		"""
		Parse the limit field, and limit the queryset
		accordingly
		"""
		limits = self.limit.split( ":" )[:2]
		try:
			start = int( limits[0] )
		except ( ValueError, IndexError ):
			start = None

		try:
			end = int( limits[1] )
		except ( ValueError, IndexError ):
			end = None

		if start is not None and end is not None:
			return qs[start:end]
		elif start is not None:
			return qs[start:]
		elif end is not None:
			return qs[:end]
		else:
			return qs

	@classmethod
	def data_sources( cls, type ):
		return cls.objects.filter( type=type )

	def get_queryset( self, ctx ):
		"""
		Get the queryset for this data source. Since a selector
		provides ability to include variables you must also
		provide a context. This is normally done by the
		newsletter generation system.
		"""
		modelcls = self.content_type.model_class()
		qs = modelcls.objects.all()

		# Run all filters
		selectors = self.selectors.all()
		if len( selectors ) > 0:
			qs = qs.filter( *[sel.get_q_object( ctx ) for sel in selectors] )

		if self.ordering:
			qs = qs.order_by( *self.ordering.get_order_by() )

		if self.limit:
			qs = self._limit_queryset( qs )

		return qs

	class Meta:
		unique_together = ( 'type', 'name' )
		ordering = ['type__name', 'title']


# =================================
# Auto generation component
# =================================
class NewsletterGenerator( object ):
	"""
	Generator for newsletters
	"""
	def __init__( self, type ):
		self.type = type

	def make_next( self, release_date ):
		"""
		Make the next issue of a newsletter (takes the start date from previous
		issue).
		"""
		latest_nl = Newsletter.latest_for_type( self.type )

		start_date = datetime.now() - timedelta( days=30 )
		if latest_nl:
			if latest_nl.end_date:
				start_date = latest_nl.end_date
			elif latest_nl.release_date:
				start_date = latest_nl.release_date

		return self.make( start_date, release_date )

	def make( self, start_date, end_date ):
		"""
		Generate an newsletter based on content published between certain dates.
		"""
		nl = Newsletter( type=self.type, published=False, release_date=end_date, start_date=start_date, end_date=end_date )
		nl.save()
		return self.update_newsletter( nl )

	def update_newsletter( self, nl ):
		"""
		Update an newsletter based on content published between certain dates.
		"""
		context = {
			'start_date': nl.start_date,
			'end_date': nl.end_date,
			'published': nl.published,
			'release_date': nl.release_date,
		}

		for src in NewsletterDataSource.data_sources( self.type ):
			for obj in src.get_queryset( context ):
				NewsletterContent.objects.get_or_create( newsletter=nl, data_source=src, object_id=obj.pk )

		for language in self.type.languages.all():
			NewsletterProxy.objects.get_or_create( id='%s-%s' % (nl.id, language.lang),
										translation_ready=True, source=nl, lang=language.lang )

		nl.save()
		return nl


# ==========================================
# Support models for MailChimpMailer plug-in
# ==========================================
class MailChimpCampaign( models.Model ):
	"""
	Model used to keep track of mailchimp campaign ids for each newsletter.
	"""
	newsletter = models.ForeignKey( Newsletter )
	list_id = models.CharField( max_length=50 )
	campaign_id = models.CharField( max_length=50 )
	lang = models.CharField( max_length=5, choices=settings.LANGUAGES, default='' )

	class Meta:
		unique_together = ['newsletter', 'list_id', 'lang']

#
# Register default mailer interfaces
#
Mailer.register_plugin( EmailMailerPlugin )
Mailer.register_plugin( MailmanMailerPlugin )

try:
	from djangoplicity.newsletters.mailers import MailChimpMailerPlugin
	Mailer.register_plugin( MailChimpMailerPlugin )
except ImportError:
	pass
