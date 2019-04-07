from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    url(r'^', include('painter.urls')),
]

urlpatterns += staticfiles_urlpatterns()
