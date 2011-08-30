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

"""

from django.db import models
from django.utils.translation import ugettext as _
from djangoplicity import archives
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.template import Context, Template
from django.contrib.sites.models import Site
from datetime import datetime, timedelta
from djangoplicity.newsletters.mailers import EmailMailerPlugin, MailerPlugin
from django.utils.functional import lazy
from django.db.models.signals import post_save

SPLIT_TEST = ( 
	( '', 'Disabled' ),
	( 'from_name', 'From' ),
	( 'subject', 'Subject' ),
 )

SPLIT_TEST_WINNER = ( 
	( 'opens', 'Opens' ),
	( 'clicks', 'Clicks' ),
 )

class Mailer( models.Model ):
	"""
	Model for defining mailers. A newsletter type can define several mailers to use
	when sending a newsletter (e.g. send newsletter via mailchimp and two other mail-man
	mailing lists. Each mailer defines the plug-in to use parameters for each plugin.
	"""
	_plugins = {}

	plugin = models.CharField( max_length=255, blank=False, choices=[] )
	name = models.CharField( max_length=255 )

	def __init__( self, *args, **kwargs ):
		"""
		"""
		super( Mailer, self ).__init__( *args, **kwargs )
		print Mailer.get_plugin_choices()
		self._meta.get_field_by_name( 'plugin' )[0]._choices = Mailer.get_plugin_choices()#lazy( Mailer.get_plugin_choices, list )

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
		return dict( [( p.name, p.get_value() ) for p in MailerParameter.objects.filter( mailer=self ) ] )

	def send_now( self, newsletter ):
		"""
		Send newsletter now via this mailer
		"""
		plugin = self.get_plugin()
		return plugin.send_now( newsletter )

	def send_test( self, newsletter, emails=[] ):
		"""
		Send test newsletter now via this mailer to listed emails
		"""
		plugin = self.get_plugin()
		return plugin.send_test( newsletter, emails )

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
		Callback to save blank value for all parameters for this plugin and remove unknown parameters
		"""
		if instance:
			known_params = dict([( p.name, p ) for p in MailerParameter.objects.filter( mailer=instance )])
			
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

post_save.connect( Mailer.post_save_handler, sender=Mailer )

class MailerParameter( models.Model ):
	"""
	Specify parameter for a mailer
	"""
	mailer = models.ForeignKey( Mailer )
	name = models.SlugField( max_length=255, unique=False )
	value = models.CharField( max_length=255, blank=True, default='' )
	type = models.CharField( max_length=4, default='str', choices=[ ( 'str', 'Text' ), ( 'int', 'Integer' ), ( 'bool', 'Boolean' ), ( 'date', 'Date' ), ] )
	help_text = models.CharField( max_length=255, blank=True )

	def get_value( self ):
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
		ordering = ['mailer','name']
		unique_together = ['mailer', 'name']

class NewsletterType( models.Model ):
	"""
	Definition of a newsletter type - e.g. ESO Outreach Community Newsletter
	"""
	#sender = ....
	#default_list =
	#mailing_list_email =
	#mailchimp_folder =
	#tracking  = models.BooleanField( default=True, help_text=_('Enable social sharing of newsletter.') )
	#analytics = models.BoeeleanField 

	#
	# Default from email/name
	#
	name = models.CharField( max_length=255 )
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
	sharing = models.BooleanField( default=True, help_text=_( 'Enable social sharing of newsletter.' ) )

	#
	# Mailers
	#
	mailers = models.ManyToManyField( Mailer, blank=True )

	def get_generator( self ):
		return NewsletterGenerator( type=self )

	def __unicode__( self ):
		return self.name

	class Meta:
		ordering = ['name']


class Newsletter( archives.ArchiveModel, models.Model ):
	"""
	"""
	# Status
	type = models.ForeignKey( NewsletterType )
	frozen = models.BooleanField( default=False )
	send = models.DateTimeField( blank=True, null=True )

	# Auto generation support
	start_date = models.DateTimeField( blank=True, null=True )
	end_date = models.DateTimeField( blank=True, null=True )

	#
	# Email
	#
	from_name = models.CharField( max_length=255, blank=True )
	from_email = models.EmailField( blank=True )

	#
	# Content
	#
	subject = models.CharField( max_length=255, blank=True )
	text = models.TextField( blank=True )
	html = models.TextField( verbose_name="HTML", blank=True )

	editorial = models.TextField( blank=True )

	#
	# A/B split testing
	#
#	split_test = models.CharField( max_length=10, blank=True, choices=SPLIT_TEST )
#	split_test_winner = models.CharField( max_length=10, blank=True, choices=SPLIT_TEST_WINNER )
#	
#	alternate_from_name = models.CharField( max_length=255 )
#	alternate_from_email = models.EmailField()
#	alternate_subject = models.CharField( max_length=255 )

	def send_now( self ):
		"""
		Send a newsletter right away.
		"""
		if self.send is None:
			self.render()
			self.frozen = True
			self.send = datetime.now()
			for m in self.type.mailers.all():
				m.send_now( self )
			self.save()
		else:
			raise Exception( "Newsletter have already been sent." )

	def send_test( self, emails ):
		"""
		Send a test version of the newsletter
		"""
		self.render()
		for m in self.type.mailers.all():
			m.send_test( self, emails )

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


	def render( self ):
		"""
		Render the newsletter
		"""
		if not self.frozen:
			t_html = Template( self.type.html_template )
			t_text = Template( self.type.text_template )
			t_subject = Template( self.type.subject_template )

			ctx = Context( {
				'base_url' : "http://%s" % Site.objects.get_current().domain,
				'data' : NewsletterContent.data_context( self ),
				'editorial' : self.editorial,
				'enable_sharing' : self.type.sharing,
				'enable_archive' : self.type.archive,
				'release_date' : self.release_date,
				'published' : self.published,
			} )

			self.html = t_html.render( ctx )
			self.text = t_text.render( ctx )
			self.subject = t_subject.render( ctx )


	def save( self, *args, **kwargs ):
		"""
		"""
		if not self.frozen:
			if self.from_name == '':
				self.from_name = self.type.default_from_name
			if self.from_email == '':
				self.from_email = self.type.default_from_email
			self.render()
		return super( Newsletter, self ).save( *args, **kwargs )

	def __unicode__( self ):
		return self.subject

	class Meta:
		pass

	class Archive:
		class Meta:
			root = ''
			release_date = True
			embargo_date = False
			last_modified = True
			created = True
			published = True


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
	def data_context( cls, newsletter ):
		"""
		Generate a data context for a newsletter
		"""
		ctx = {}

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
					else:
						if len( allpks ) > 0:
							data = modelcls.objects.get( pk=allpks[0] )
				except modelcls.DoesNotExist:
					data = None

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
		return { str( "%s__%s" % ( self.field, self.match ) ) : self.get_value( ctx )  }

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
	Specifies data sources and names for
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
			'start_date' : nl.start_date,
			'end_date' : nl.end_date,
			'published' : nl.published,
			'release_date' : nl.release_date,
		}

		for src in NewsletterDataSource.data_sources( self.type ):
			for obj in src.get_queryset( context ):
				( content_obj, created ) = NewsletterContent.objects.get_or_create( newsletter=nl, data_source=src, object_id=obj.pk )

		nl.save()
		return nl



#
# Register default mailer interfaces
#
Mailer.register_plugin( EmailMailerPlugin )
