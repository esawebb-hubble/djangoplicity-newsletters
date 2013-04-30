# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Language.default_from_name'
        db.add_column('newsletters_language', 'default_from_name',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Language.default_from_email'
        db.add_column('newsletters_language', 'default_from_email',
                      self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Language.default_from_name'
        db.delete_column('newsletters_language', 'default_from_name')

        # Deleting field 'Language.default_from_email'
        db.delete_column('newsletters_language', 'default_from_email')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'newsletters.datasourceordering': {
            'Meta': {'ordering': "['name']", 'object_name': 'DataSourceOrdering'},
            'fields': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'newsletters.datasourceselector': {
            'Meta': {'ordering': "['name']", 'object_name': 'DataSourceSelector'},
            'field': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'filter': ('django.db.models.fields.CharField', [], {'default': "'I'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'str'", 'max_length': '4'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'newsletters.language': {
            'Meta': {'object_name': 'Language'},
            'default_from_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'default_from_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '5', 'primary_key': 'True'})
        },
        'newsletters.mailchimpcampaign': {
            'Meta': {'unique_together': "(['newsletter', 'list_id', 'lang'],)", 'object_name': 'MailChimpCampaign'},
            'campaign_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '5'}),
            'list_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Newsletter']"})
        },
        'newsletters.mailer': {
            'Meta': {'ordering': "['name']", 'object_name': 'Mailer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'plugin': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'newsletters.mailerlog': {
            'Meta': {'ordering': "['-timestamp']", 'object_name': 'MailerLog'},
            'error': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'newsletter_pk': ('django.db.models.fields.IntegerField', [], {}),
            'parameters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'plugin': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'success': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'newsletters.mailerparameter': {
            'Meta': {'ordering': "['mailer', 'name']", 'unique_together': "(['mailer', 'name'],)", 'object_name': 'MailerParameter'},
            'help_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Mailer']"}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'str'", 'max_length': '4'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        'newsletters.newsletter': {
            'Meta': {'ordering': "['-release_date']", 'object_name': 'Newsletter'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'editorial': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            'editorial_subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'editorial_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'from_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'from_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.SlugField', [], {'default': "'289'", 'max_length': '50', 'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '5', 'db_index': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'release_date': ('djangoplicity.archives.fields.ReleaseDateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'scheduled_status': ('django.db.models.fields.CharField', [], {'default': "'OFF'", 'max_length': '10'}),
            'scheduled_task_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'send': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('djangoplicity.translation.fields.TranslationForeignKey', [], {'blank': 'True', 'related_name': "'translations'", 'null': 'True', 'only_sources': 'False', 'to': "orm['newsletters.Newsletter']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'translation_ready': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterType']"})
        },
        'newsletters.newslettercontent': {
            'Meta': {'ordering': "['newsletter', 'data_source', 'object_id']", 'object_name': 'NewsletterContent'},
            'data_source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterDataSource']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Newsletter']"}),
            'object_id': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'newsletters.newsletterdatasource': {
            'Meta': {'ordering': "['type__name', 'title']", 'unique_together': "(('type', 'name'),)", 'object_name': 'NewsletterDataSource'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'limit': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'list': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'ordering': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.DataSourceOrdering']", 'null': 'True', 'blank': 'True'}),
            'selectors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletters.DataSourceSelector']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterType']"})
        },
        'newsletters.newslettertype': {
            'Meta': {'ordering': "['name']", 'object_name': 'NewsletterType'},
            'archive': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'default_from_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'default_from_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'html_template': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'languages': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletters.Language']", 'symmetrical': 'False', 'blank': 'True'}),
            'local_archive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mailers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletters.Mailer']", 'symmetrical': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sharing': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'subject_template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'subscribe_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'text_template': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['newsletters']