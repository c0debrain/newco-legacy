from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to

from django.contrib import admin
admin.autodiscover()

from pinax.apps.account.openid_consumer import PinaxConsumer
from newco.views import HomePageRedirectView


handler500 = "pinax.views.server_error"


urlpatterns = patterns("",
    url(r"^$", HomePageRedirectView.as_view(), name="home"),
    url(r"^admin/invite_user/$",
                "pinax.apps.signup_codes.views.admin_invite_user",
                name="admin_invite_user"
    ),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^about/", include("about.urls")),
    url(r"^account/", include("pinax.apps.account.urls")),
    url(r"^openid/", include(PinaxConsumer().urls)),
#    url(r"^notices/", include("notification.urls")),
    url(r"^announcements/", include("announcements.urls")),
    url(r"^content/", include("items.urls")),
    url(r"^profiles/", include("profiles.urls")),
    url(r"^profiles/", include("idios.urls")),
    url(r"^votes/", include('votes.urls')),
    url(r"^follow/", include('follow.urls')),
)

urlpatterns += patterns("",
    url(r"^Friends/(?P<path>.*)$", redirect_to, {
            'url': 'http://static.newco-project.fr/Friends/%(path)s',
            'permanent': True
        }
    ),
    url(r"^static/(?P<path>.*)$", redirect_to, {
            'url': 'http://static.newco-project.fr/static/%(path)s',
            'permanent': True
        }
    ),
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        url(r"", include("staticfiles.urls")),
    )
