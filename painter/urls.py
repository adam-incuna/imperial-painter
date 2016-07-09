from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views


urlpatterns = [
    url(r'^noreload$', views.CardDisplay.as_view(), name='card_display_noreload'),
    url(r'^$', views.CardDisplayReload.as_view(), name='card_display_reload'),
]

urlpatterns += staticfiles_urlpatterns()
