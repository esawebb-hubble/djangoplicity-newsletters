import django.contrib.auth.admin
import django.contrib.redirects.admin
import django.contrib.sites.admin
# import djangoplicity.actions.admin
import djangoplicity.media.admin
import djangoplicity.menus.admin
import djangoplicity.metadata.admin
import djangoplicity.pages.admin
import djangoplicity.releases.admin
import djangoplicity.reports.admin
import djangoplicity.science.admin
# Products imports
from djangoplicity.contrib.admin import DjangoplicityModelAdmin
from djangoplicity.contrib.admin.discover import autoregister
from djangoplicity.contrib.admin.discover import autoregister
from djangoplicity.contrib.admin.sites import AdminSite
from djangoplicity.contrib.admin.sites import AdminSite

import djangoplicity.mailinglists.admin
import djangoplicity.newsletters.admin
import djangoplicity.newsletters.admin

# Register each applications admin interfaces with
# an admin site.
admin_site = AdminSite(name="admin_site")
adminlogs_site = AdminSite(name="adminlogs_site")

autoregister(admin_site, djangoplicity.announcements.admin)
# autoregister(adminlogs_site, djangoplicity.actions.admin)
autoregister(admin_site, django.contrib.auth.admin)
autoregister(admin_site, django.contrib.sites.admin)
autoregister(admin_site, djangoplicity.menus.admin)
autoregister(admin_site, djangoplicity.pages.admin)
autoregister(admin_site, djangoplicity.media.admin)
autoregister(admin_site, djangoplicity.releases.admin)
autoregister(admin_site, djangoplicity.metadata.admin)
autoregister(admin_site, djangoplicity.mailinglists.admin)
autoregister(admin_site, djangoplicity.newsletters.admin)
autoregister(admin_site, djangoplicity.science.admin)

#
# Applications that does not support above method.
#
djangoplicity.reports.admin.advanced_register_with_admin(admin_site)

adminlogs_site.register(django.contrib.redirects.models.Redirect, django.contrib.redirects.admin.RedirectAdmin)

adminlogs_site.register(django.contrib.sites.models.Site, django.contrib.sites.admin.SiteAdmin)

admin_site.register(django.contrib.auth.models.User, django.contrib.auth.admin.UserAdmin)

admin_site.register(django.contrib.auth.models.Group, django.contrib.auth.admin.GroupAdmin)
