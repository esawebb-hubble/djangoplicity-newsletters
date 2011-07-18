# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BadEmailAddress'
        db.create_table('newsletters_bademailaddress', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('newsletters', ['BadEmailAddress'])

        # Adding model 'Subscriber'
        db.create_table('newsletters_subscriber', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
        ))
        db.send_create_signal('newsletters', ['Subscriber'])

        # Adding model 'List'
        db.create_table('newsletters_list', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('password', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('newsletters', ['List'])

        # Adding model 'Subscription'
        db.create_table('newsletters_subscription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subscriber', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.Subscriber'])),
            ('list', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.List'])),
        ))
        db.send_create_signal('newsletters', ['Subscription'])

        # Adding unique constraint on 'Subscription', fields ['subscriber', 'list']
        db.create_unique('newsletters_subscription', ['subscriber_id', 'list_id'])

        # Adding model 'MailChimpList'
        db.create_table('newsletters_mailchimplist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('api_key', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
            ('list_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('web_id', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('email_type_option', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('use_awesomebar', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('default_from_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('default_from_email', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('default_subject', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('default_language', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('list_rating', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('member_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('unsubscribe_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('cleaned_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('member_count_since_send', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('unsubscribe_count_since_send', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('cleaned_count_since_send', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('avg_sub_rate', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('avg_unsub_rate', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('target_sub_rate', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('open_rate', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('click_rate', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('connected', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_sync', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('newsletters', ['MailChimpList'])

        # Adding model 'MailChimpSubscriberExclude'
        db.create_table('newsletters_mailchimpsubscriberexclude', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mailchimplist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.MailChimpList'])),
            ('subscriber', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.Subscriber'])),
        ))
        db.send_create_signal('newsletters', ['MailChimpSubscriberExclude'])

        # Adding unique constraint on 'MailChimpSubscriberExclude', fields ['mailchimplist', 'subscriber']
        db.create_unique('newsletters_mailchimpsubscriberexclude', ['mailchimplist_id', 'subscriber_id'])

        # Adding model 'MailChimpSourceList'
        db.create_table('newsletters_mailchimpsourcelist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mailchimplist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.MailChimpList'])),
            ('list', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.List'])),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('newsletters', ['MailChimpSourceList'])

        # Adding unique constraint on 'MailChimpSourceList', fields ['mailchimplist', 'list']
        db.create_unique('newsletters_mailchimpsourcelist', ['mailchimplist_id', 'list_id'])

        # Adding model 'MailChimpListToken'
        db.create_table('newsletters_mailchimplisttoken', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('list', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.MailChimpList'])),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
            ('token', self.gf('django.db.models.fields.CharField')(unique=True, max_length=56)),
            ('expired', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('newsletters', ['MailChimpListToken'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'MailChimpSourceList', fields ['mailchimplist', 'list']
        db.delete_unique('newsletters_mailchimpsourcelist', ['mailchimplist_id', 'list_id'])

        # Removing unique constraint on 'MailChimpSubscriberExclude', fields ['mailchimplist', 'subscriber']
        db.delete_unique('newsletters_mailchimpsubscriberexclude', ['mailchimplist_id', 'subscriber_id'])

        # Removing unique constraint on 'Subscription', fields ['subscriber', 'list']
        db.delete_unique('newsletters_subscription', ['subscriber_id', 'list_id'])

        # Deleting model 'BadEmailAddress'
        db.delete_table('newsletters_bademailaddress')

        # Deleting model 'Subscriber'
        db.delete_table('newsletters_subscriber')

        # Deleting model 'List'
        db.delete_table('newsletters_list')

        # Deleting model 'Subscription'
        db.delete_table('newsletters_subscription')

        # Deleting model 'MailChimpList'
        db.delete_table('newsletters_mailchimplist')

        # Deleting model 'MailChimpSubscriberExclude'
        db.delete_table('newsletters_mailchimpsubscriberexclude')

        # Deleting model 'MailChimpSourceList'
        db.delete_table('newsletters_mailchimpsourcelist')

        # Deleting model 'MailChimpListToken'
        db.delete_table('newsletters_mailchimplisttoken')


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
