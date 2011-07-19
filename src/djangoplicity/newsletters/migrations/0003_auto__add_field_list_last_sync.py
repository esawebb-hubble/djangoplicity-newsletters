# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'List.last_sync'
        db.add_column('newsletters_list', 'last_sync', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'List.last_sync'
        db.delete_column('newsletters_list', 'last_sync')


    models = {
        'newsletters.bademailaddress': {
            'Meta': {'ordering': "('email',)", 'object_name': 'BadEmailAddress'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'newsletters.list': {
            'Meta': {'ordering': "('name',)", 'object_name': 'List'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'password': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletters.Subscriber']", 'symmetrical': 'False', 'through': "orm['newsletters.Subscription']", 'blank': 'True'})
        },
        'newsletters.mailchimplist': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MailChimpList'},
            'api_key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'avg_sub_rate': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'avg_unsub_rate': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'cleaned_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'cleaned_count_since_send': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'click_rate': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'connected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_from_email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'default_from_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'default_language': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'default_subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'email_type_option': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'list_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'list_rating': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'member_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'member_count_since_send': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'open_rate': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletters.List']", 'through': "orm['newsletters.MailChimpSourceList']", 'symmetrical': 'False'}),
            'subscriber_excludes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['newsletters.Subscriber']", 'through': "orm['newsletters.MailChimpSubscriberExclude']", 'symmetrical': 'False'}),
            'synchronize': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'target_sub_rate': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'unsubscribe_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'unsubscribe_count_since_send': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'use_awesomebar': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'web_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'newsletters.mailchimplisttoken': {
            'Meta': {'object_name': 'MailChimpListToken'},
            'expired': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.MailChimpList']"}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '56'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'})
        },
        'newsletters.mailchimpsourcelist': {
            'Meta': {'unique_together': "(('mailchimplist', 'list'),)", 'object_name': 'MailChimpSourceList'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.List']"}),
            'mailchimplist': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.MailChimpList']"})
        },
        'newsletters.mailchimpsubscriberexclude': {
            'Meta': {'unique_together': "(('mailchimplist', 'subscriber'),)", 'object_name': 'MailChimpSubscriberExclude'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailchimplist': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.MailChimpList']"}),
            'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Subscriber']"})
        },
        'newsletters.subscriber': {
            'Meta': {'ordering': "('email',)", 'object_name': 'Subscriber'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'newsletters.subscription': {
            'Meta': {'ordering': "('subscriber__email',)", 'unique_together': "(('subscriber', 'list'),)", 'object_name': 'Subscription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.List']"}),
            'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Subscriber']"})
        }
    }

    complete_apps = ['newsletters']
