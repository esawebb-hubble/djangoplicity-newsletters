# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MailChimpEventAction'
        db.create_table('mailinglists_mailchimpeventaction', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['actions.Action'])),
            ('on_event', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('model_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mailinglists.MailChimpList'])),
        ))
        db.send_create_signal('mailinglists', ['MailChimpEventAction'])


    def backwards(self, orm):
        
        # Deleting model 'MailChimpEventAction'
        db.delete_table('mailinglists_mailchimpeventaction')


    models = {
        'actions.action': {
            'Meta': {'ordering': "['name']", 'object_name': 'Action'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'plugin': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
        'mailinglists.mailchimpeventaction': {
            'Meta': {'object_name': 'MailChimpEventAction'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['actions.Action']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mailinglists.MailChimpList']"}),
            'on_event': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
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
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
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
            'primary_key_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mailinglists.MailChimpMergeVar']", 'null': 'True', 'blank': 'True'}),
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
        'mailinglists.mailchimpmergevar': {
            'Meta': {'object_name': 'MailChimpMergeVar'},
            'choices': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'default': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mailinglists.MailChimpList']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'mailinglists.mergevarmapping': {
            'Meta': {'object_name': 'MergeVarMapping'},
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mailinglists.MailChimpList']"}),
            'merge_var': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mailinglists.MailChimpMergeVar']"})
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
