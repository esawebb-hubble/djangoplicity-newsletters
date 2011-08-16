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

SPLIT_TEST = ( 
	( '', 'Disabled' ),
	( 'from_name', 'From' ),
	( 'subject', 'Subject' ),
 )

SPLIT_TEST_WINNER = ( 
	( 'opens', 'Opens' ),
	( 'clicks', 'Clicks' ),
 )

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

	def __unicode__( self ):
		return self.name


class Newsletter( archives.ArchiveModel, models.Model ):
	"""
	"""
	type = models.ForeignKey( NewsletterType )

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

	def render( self ):
		"""
		Render the newsletter
		"""
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

	#def clean_fields( self, exclude=None ):
	#	"""
	#	"""
	#	super( Newsletter, self ).clean_fields( exclude=exclude )

	def save( self, *args, **kwargs ):
		"""
		"""
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


#	def send()
#	
#	def send_test()
#	
#	def update()
#	
#	def render()
#		
#		
#	def schedule()


class NewsletterContent( models.Model ):
	"""
	Specifies content for a specific newsletter. Note, that 
	only content objects of allowed content types will be
	available in the templates.
	"""
	newsletter = models.ForeignKey( Newsletter )
	content_type = models.ForeignKey( ContentType )
	object_id = models.SlugField( primary_key=False )
	subgroup = models.SlugField( blank=True )
	content_object = generic.GenericForeignKey( 'content_type', 'object_id' )

	class Meta:
		ordering = ['newsletter', 'content_type', 'object_id', 'subgroup']

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

			content_objects = cls.objects.filter( newsletter=newsletter, content_type=datasrc.content_type )

			# Make dictionary of groups with empty lists as values 
			groups = dict( [( g, [] ) for g in filter( lambda x: x != "", set( [obj.subgroup for obj in content_objects] ) )] )
			
			allpks = []
			for obj in content_objects:
				allpks.append( obj.object_id )
				if obj.subgroup:
					groups[obj.subgroup].append( obj.object_id )

			try:
				if datasrc.list:
					data = modelcls.objects.filter( pk__in=allpks )
					
					# Create groups if needed.
					if len( groups.keys() ) > 0:
						data = { 'all' : data }
						for g, gpks in groups.items():
							data[g] = filter( lambda o: o.pk in gpks, data['all'] )
				else:
					if len( allpks ) > 0:
						data = modelcls.objects.get( pk=allpks[0] )
			except modelcls.DoesNotExist:
				data = None

			ctx[datasrc.name] = data
		return ctx


class NewsletterDataSource( models.Model ):
	"""
	Specifies data sources and names for
	"""
	type = models.ForeignKey( NewsletterType )
	name = models.SlugField( help_text=_( 'Name used to access this data source in templates' ) )
	title = models.CharField( max_length=255 )
	content_type = models.ForeignKey( ContentType )
	list = models.BooleanField( default=True )

	def __unicode__( self ):
		return self.title

	@classmethod
	def data_sources( cls, type ):
		return cls.objects.filter( type=type )

	class Meta:
		unique_together = ( 'type', 'name' )










