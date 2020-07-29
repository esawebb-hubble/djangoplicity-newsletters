import django.contrib.auth.admin
import django.contrib.redirects.admin
import django.contrib.sites.admin
import djangoplicity.actions.admin
from djangoplicity.contrib.admin.discover import autoregister
from djangoplicity.contrib.admin.sites import AdminSite

import djangoplicity.mailinglists.admin
import djangoplicity.newsletters.admin

# Register each applications admin interfaces with
# an admin site.
admin_site = AdminSite(name="admin_site")
adminlogs_site = AdminSite(name="adminlogs_site")
adminshop_site = AdminSite(name="adminshop_site")

autoregister(admin_site, django.contrib.auth.admin)
autoregister(admin_site, django.contrib.sites.admin)

autoregister(admin_site, djangoplicity.mailinglists.admin)
autoregister(admin_site, djangoplicity.newsletters.admin)
autoregister(adminlogs_site, djangoplicity.actions.admin)

#
# Applications that does not support above method.
#
djangoplicity.reports.admin.advanced_register_with_admin(admin_site)

adminlogs_site.register(django.contrib.redirects.models.Redirect, django.contrib.redirects.admin.RedirectAdmin)

adminlogs_site.register(django.contrib.sites.models.Site, django.contrib.sites.admin.SiteAdmin)

admin_site.register(django.contrib.auth.models.User, django.contrib.auth.admin.UserAdmin)

admin_site.register(django.contrib.auth.models.Group, django.contrib.auth.admin.GroupAdmin)
