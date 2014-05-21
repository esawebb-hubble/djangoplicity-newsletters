# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

	def forwards(self, orm):
		
		# Removing unique constraint on 'NewsletterContent', fields ['object_id']
		# db.delete_primary_key('newsletters_newslettercontent')
		
		# Changing field 'NewsletterContent.object_id'
		db.alter_column('newsletters_newslettercontent', 'object_id', self.gf('django.db.models.fields.SlugField')(max_length=50))

		# Adding field 'NewsletterContent.id'
		db.add_column('newsletters_newslettercontent', 'id', self.gf('django.db.models.fields.AutoField')(primary_key=True), keep_default=False)

		


	def backwards(self, orm):
		pass

#		raise RuntimeError("Backwards migration not supported.")

	models = {
		'contenttypes.contenttype': {
			'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
			'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
		},
		'newsletters.newsletter': {
			'Meta': {'object_name': 'Newsletter'},
			'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
			'from_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
			'from_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
			'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
			'published': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
			'release_date': ('djangoplicity.archives.fields.ReleaseDateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
			'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
			'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
			'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterType']"})
		},
		'newsletters.newslettercontent': {
			'Meta': {'ordering': "['newsletter', 'content_type', 'object_id', 'subgroup']", 'object_name': 'NewsletterContent'},
			'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Newsletter']"}),
			'object_id': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
			'subgroup': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
		},
		'newsletters.newsletterdatasource': {
			'Meta': {'unique_together': "(('type', 'name'),)", 'object_name': 'NewsletterDataSource'},
			'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'list': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
			'name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
			'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
			'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterType']"})
		},
		'newsletters.newslettertype': {
			'Meta': {'object_name': 'NewsletterType'},
			'archive': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
			'default_from_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
			'default_from_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
			'html_template': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
			'sharing': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
			'subject_template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
			'text_template': ('django.db.models.fields.TextField', [], {'blank': 'True'})
		}
	}

	complete_apps = ['newsletters']
