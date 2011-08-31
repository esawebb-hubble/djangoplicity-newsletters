# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding unique constraint on 'MailerParameter', fields ['mailer', 'name']
        db.create_unique('newsletters_mailerparameter', ['mailer_id', 'name'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'MailerParameter', fields ['mailer', 'name']
        db.delete_unique('newsletters_mailerparameter', ['mailer_id', 'name'])


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
            'fields': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'newsletters.datasourceselector': {
            'Meta': {'ordering': "['name']", 'object_name': 'DataSourceSelector'},
            'field': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'filter': ('django.db.models.fields.CharField', [], {'default': "'I'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'str'", 'max_length': '4'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'newsletters.mailer': {
            'Meta': {'ordering': "['name']", 'object_name': 'Mailer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'plugin': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'newsletters.mailerparameter': {
            'Meta': {'ordering': "['mailer', 'name']", 'unique_together': "(['mailer', 'name'],)", 'object_name': 'MailerParameter'},
            'help_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Mailer']"}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'str'", 'max_length': '4'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        'newsletters.newsletter': {
            'Meta': {'object_name': 'Newsletter'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'editorial': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'from_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'from_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'frozen': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'release_date': ('djangoplicity.archives.fields.ReleaseDateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'send': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterType']"})
        },
        'newsletters.newslettercontent': {
            'Meta': {'ordering': "['newsletter', 'data_source', 'object_id']", 'object_name': 'NewsletterContent'},
            'data_source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterDataSource']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Newsletter']"}),
            'object_id': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'newsletters.newsletterdatasource': {
            'Meta': {'ordering': "['type__name', 'title']", 'unique_together': "(('type', 'name'),)", 'object_name': 'NewsletterDataSource'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'limit': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'list': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
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
            'mailers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletters.Mailer']", 'symmetrical': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sharing': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'subject_template': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'text_template': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['newsletters']
