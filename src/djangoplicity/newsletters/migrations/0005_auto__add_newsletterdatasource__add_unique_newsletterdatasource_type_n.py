# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'NewsletterDataSource'
        db.create_table('newsletters_newsletterdatasource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.NewsletterType'])),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('list', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('newsletters', ['NewsletterDataSource'])

        # Adding unique constraint on 'NewsletterDataSource', fields ['type', 'name']
        db.create_unique('newsletters_newsletterdatasource', ['type_id', 'name'])

        # Adding model 'Newsletter'
        db.create_table('newsletters_newsletter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.NewsletterType'])),
            ('from_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('from_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('html', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('release_date', self.gf('djangoplicity.archives.fields.ReleaseDateTimeField')(db_index=True, null=True, blank=True)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('newsletters', ['Newsletter'])

        # Adding model 'NewsletterContent'
        db.create_table('newsletters_newslettercontent', (
            ('newsletter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.Newsletter'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('djangoplicity.archives.fields.IdField')(max_length=50, primary_key=True, db_index=True)),
        ))
        db.send_create_signal('newsletters', ['NewsletterContent'])

        # Adding model 'NewsletterType'
        db.create_table('newsletters_newslettertype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('default_from_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('default_from_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('subject_template', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('text_template', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('html_template', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('archive', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('sharing', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('newsletters', ['NewsletterType'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'NewsletterDataSource', fields ['type', 'name']
        db.delete_unique('newsletters_newsletterdatasource', ['type_id', 'name'])

        # Deleting model 'NewsletterDataSource'
        db.delete_table('newsletters_newsletterdatasource')

        # Deleting model 'Newsletter'
        db.delete_table('newsletters_newsletter')

        # Deleting model 'NewsletterContent'
        db.delete_table('newsletters_newslettercontent')

        # Deleting model 'NewsletterType'
        db.delete_table('newsletters_newslettertype')


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
            'from_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'from_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'release_date': ('djangoplicity.archives.fields.ReleaseDateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterType']"})
        },
        'newsletters.newslettercontent': {
            'Meta': {'object_name': 'NewsletterContent'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Newsletter']"}),
            'object_id': ('djangoplicity.archives.fields.IdField', [], {'max_length': '50', 'primary_key': 'True', 'db_index': 'True'})
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
