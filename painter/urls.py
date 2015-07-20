from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.CardDisplay.as_view(), name='card_display')
]
