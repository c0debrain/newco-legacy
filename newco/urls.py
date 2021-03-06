from django.conf import settings
from django.conf.urls import patterns, include, url
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView

from django.contrib import admin
admin.autodiscover()

from sitemaps import all_sitemaps as sitemaps
from tastypie.api import Api

from content.api import ItemResource, RelationResource
from views import HomepageView


def google_webmaster_view(request):
    return HttpResponse("google-site-verification: google009a062b2cd3a7e6.html")

v1_api = Api(api_name='v1')
v1_api.register(ItemResource())
v1_api.register(RelationResource())

urlpatterns = patterns("",
    url(r"^$", HomepageView.as_view(), {"choose_community": True}, name="home"),
    url(r"^(?P<cat>products|questions)$", HomepageView.as_view(), name="home"),
    url(r"^(?P<cat>products|questions)/(?P<filter>last|popular|unanswered)$",
        HomepageView.as_view(), name="home"),
    url(r"^content$", HomepageView.as_view(), name="item_index"),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^admin_tools/", include("admin_tools.urls")),
    url(r"^about/", include("about.urls")),
    url(r"^account/", include("custaccount.urls")),
    # url(r"^announcements/", include("announcements.urls")),
    url(r"^content/", include("items.urls")),
    url(r"^dashboard", include("dashboard.urls")),
    url(r"^content2/", include("content.urls")),
    url(r'^api/', include(v1_api.urls)),
    url(r"^profiles/", include("profiles.urls")),
    url(r"^utils", include("utils.urls")),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.index', {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
)

urlpatterns += patterns("", url(r"^google009a062b2cd3a7e6.html", google_webmaster_view))

if settings.DEBUG:
    urlpatterns += patterns("", url(r"^rosetta/", include("rosetta.urls")))
    from utils import jsreverse
    jsreverse.save_static_urls_js(settings.PROJECT_ROOT)


urlpatterns += patterns("",
    url(r"^static/(?P<path>.*)$", RedirectView.as_view(
        url="http://static.newco-project.fr/static/%(path)s", permanent=True)),
    url(r"^(.)riends/(?P<path>.*)$", RedirectView.as_view(
        url="http://static.newco-project.fr/Friends/%(path)s", permanent=True))
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns("", url(r"", include("staticfiles.urls")))
