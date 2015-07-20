from django.views.generic import ListView

from . import models


class CardDisplay(ListView):
    model = models.Card
    template_name = 'painter/card_display.html'
