# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'MailChimpSubscriberExclude', fields ['mailchimplist', 'subscriber']
        db.delete_unique('mailinglists_mailchimpsubscriberexclude', ['mailchimplist_id', 'subscriber_id'])

        # Removing unique constraint on 'MailChimpSourceList', fields ['mailchimplist', 'list']
        db.delete_unique('mailinglists_mailchimpsourcelist', ['mailchimplist_id', 'list_id'])

        # Deleting model 'MailChimpSourceList'
        db.delete_table('mailinglists_mailchimpsourcelist')

        # Deleting model 'MailChimpSubscriberExclude'
        db.delete_table('mailinglists_mailchimpsubscriberexclude')


    def backwards(self, orm):
        
        # Adding model 'MailChimpSourceList'
        db.create_table('mailinglists_mailchimpsourcelist', (
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('list', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mailinglists.List'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mailchimplist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mailinglists.MailChimpList'])),
        ))
        db.send_create_signal('mailinglists', ['MailChimpSourceList'])

        # Adding unique constraint on 'MailChimpSourceList', fields ['mailchimplist', 'list']
        db.create_unique('mailinglists_mailchimpsourcelist', ['mailchimplist_id', 'list_id'])

        # Adding model 'MailChimpSubscriberExclude'
        db.create_table('mailinglists_mailchimpsubscriberexclude', (
            ('subscriber', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mailinglists.Subscriber'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mailchimplist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mailinglists.MailChimpList'])),
        ))
        db.send_create_signal('mailinglists', ['MailChimpSubscriberExclude'])

        # Adding unique constraint on 'MailChimpSubscriberExclude', fields ['mailchimplist', 'subscriber']
        db.create_unique('mailinglists_mailchimpsubscriberexclude', ['mailchimplist_id', 'subscriber_id'])


    models = {
        'mailinglists.bademailaddress': {
            'Meta': {'ordering': "('email',)", 'object_name': 'BadEmailAddress'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'mailinglists.list': {
            'Meta': {'ordering': "('name',)", 'object_name': 'List'},
            'base_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'password': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['mailinglists.Subscriber']", 'symmetrical': 'False', 'through': "orm['mailinglists.Subscription']", 'blank': 'True'})
        },
        'mailinglists.mailchimplist': {
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
            'synchronize': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'target_sub_rate': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'unsubscribe_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'unsubscribe_count_since_send': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'use_awesomebar': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'web_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'mailinglists.mailchimplisttoken': {
            'Meta': {'object_name': 'MailChimpListToken'},
            'expired': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mailinglists.MailChimpList']"}),
            'token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '56'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'})
        },
        'mailinglists.subscriber': {
            'Meta': {'ordering': "('email',)", 'object_name': 'Subscriber'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'mailinglists.subscription': {
            'Meta': {'ordering': "('subscriber__email',)", 'unique_together': "(('subscriber', 'list'),)", 'object_name': 'Subscription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mailinglists.List']"}),
            'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mailinglists.Subscriber']"})
        }
    }

    complete_apps = ['mailinglists']
