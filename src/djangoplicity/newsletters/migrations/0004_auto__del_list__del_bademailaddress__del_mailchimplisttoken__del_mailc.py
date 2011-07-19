# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
	depends_on = (
		( "mailinglists", "0001_initial" ),
	)
	
	def forwards(self, orm):
		# Deleting model 'List'
		db.delete_table('mailinglists_list')
		db.rename_table('newsletters_list','mailinglists_list')

		# Deleting model 'BadEmailAddress'
		db.delete_table('mailinglists_bademailaddress')
		db.rename_table('newsletters_bademailaddress','mailinglists_bademailaddress')

		# Deleting model 'MailChimpListToken'
		db.delete_table('mailinglists_mailchimplisttoken')
		db.rename_table('newsletters_mailchimplisttoken','mailinglists_mailchimplisttoken')

		# Deleting model 'MailChimpSubscriberExclude'
		db.delete_table('mailinglists_mailchimpsubscriberexclude')
		db.rename_table('newsletters_mailchimpsubscriberexclude','mailinglists_mailchimpsubscriberexclude')

		# Deleting model 'Subscriber'
		db.delete_table('mailinglists_subscriber')
		db.rename_table('newsletters_subscriber','mailinglists_subscriber')

		# Deleting model 'MailChimpList'
		db.delete_table('mailinglists_mailchimplist')
		db.rename_table('newsletters_mailchimplist','mailinglists_mailchimplist')

		# Deleting model 'MailChimpSourceList'
		db.delete_table('mailinglists_mailchimpsourcelist')
		db.rename_table('newsletters_mailchimpsourcelist','mailinglists_mailchimpsourcelist')

		# Deleting model 'Subscription'
		db.delete_table('mailinglists_subscription')
		db.rename_table('newsletters_subscription','mailinglists_subscription')


	def backwards(self, orm):
		raise RuntimeError( "Backwards migration not allowed" )


	models = {
		
	}

	complete_apps = ['newsletters']
