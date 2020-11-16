"""test_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from djangoplicity.newsletters.models import Newsletter
from djangoplicity.newsletters.options import NewsletterOptions
from test_project.admin import admin_site, adminlogs_site

urlpatterns = [
    url(r'^admin/', admin_site.urls, {'extra_context': {'ADMIN_SITE': True}}),
    url(r'^admin/system/', adminlogs_site.urls, {'extra_context': {'ADMINLOGS_SITE': True}}),
    url(r'^tinymce/', include('tinymce.urls')),
    url(
        r'^newsletters/',
        include(
            ('djangoplicity.mailinglists.urls', 'djangoplicity_mailinglists',),
            namespace='djangoplicity_mailinglists'
        )
    ),
    url(
        r'^newsletters/',
        include('djangoplicity.newsletters.urls'),
        {'model': Newsletter, 'options': NewsletterOptions, }
    ),
]
