# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DataSourceOrdering'
        db.create_table('newsletters_datasourceordering', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=255, db_index=True)),
            ('fields', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('newsletters', ['DataSourceOrdering'])

        # Adding model 'DataSourceSelector'
        db.create_table('newsletters_datasourceselector', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('filter', self.gf('django.db.models.fields.CharField')(default='I', max_length=1)),
            ('field', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('match', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('newsletters', ['DataSourceSelector'])

        # Adding field 'NewsletterDataSource.ordering'
        db.add_column('newsletters_newsletterdatasource', 'ordering', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.DataSourceOrdering'], null=True, blank=True), keep_default=False)

        # Adding field 'NewsletterDataSource.limit'
        db.add_column('newsletters_newsletterdatasource', 'limit', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True), keep_default=False)

        # Adding M2M table for field selectors on 'NewsletterDataSource'
        db.create_table('newsletters_newsletterdatasource_selectors', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('newsletterdatasource', models.ForeignKey(orm['newsletters.newsletterdatasource'], null=False)),
            ('datasourceselector', models.ForeignKey(orm['newsletters.datasourceselector'], null=False))
        ))
        db.create_unique('newsletters_newsletterdatasource_selectors', ['newsletterdatasource_id', 'datasourceselector_id'])

        # Adding field 'Newsletter.frozen'
        db.add_column('newsletters_newsletter', 'frozen', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'Newsletter.start_date'
        db.add_column('newsletters_newsletter', 'start_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'Newsletter.end_date'
        db.add_column('newsletters_newsletter', 'end_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'NewsletterContent.data_source'
        db.add_column('newsletters_newslettercontent', 'data_source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletters.NewsletterDataSource'], null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'DataSourceOrdering'
        db.delete_table('newsletters_datasourceordering')

        # Deleting model 'DataSourceSelector'
        db.delete_table('newsletters_datasourceselector')

        # Deleting field 'NewsletterDataSource.ordering'
        db.delete_column('newsletters_newsletterdatasource', 'ordering_id')

        # Deleting field 'NewsletterDataSource.limit'
        db.delete_column('newsletters_newsletterdatasource', 'limit')

        # Removing M2M table for field selectors on 'NewsletterDataSource'
        db.delete_table('newsletters_newsletterdatasource_selectors')

        # Deleting field 'Newsletter.frozen'
        db.delete_column('newsletters_newsletter', 'frozen')

        # Deleting field 'Newsletter.start_date'
        db.delete_column('newsletters_newsletter', 'start_date')

        # Deleting field 'Newsletter.end_date'
        db.delete_column('newsletters_newsletter', 'end_date')

        # Deleting field 'NewsletterContent.data_source'
        db.delete_column('newsletters_newslettercontent', 'data_source_id')


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
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'newsletters.datasourceselector': {
            'Meta': {'ordering': "['name']", 'object_name': 'DataSourceSelector'},
            'field': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'filter': ('django.db.models.fields.CharField', [], {'default': "'I'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterType']"})
        },
        'newsletters.newslettercontent': {
            'Meta': {'ordering': "['newsletter', 'content_type', 'object_id', 'subgroup']", 'object_name': 'NewsletterContent'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'data_source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.NewsletterDataSource']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['newsletters.Newsletter']"}),
            'object_id': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'subgroup': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'})
        },
        'newsletters.newsletterdatasource': {
            'Meta': {'unique_together': "(('type', 'name'),)", 'object_name': 'NewsletterDataSource'},
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
