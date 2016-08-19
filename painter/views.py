from django.views.generic import ListView

from . import models
from .management.commands import import_cards


class CardDisplay(ListView):
    model = models.Card
    template_name = 'painter/card_display.html'


class CardDisplayReload(CardDisplay):
    def get(self, request, *args, **kwargs):
        importer = import_cards.Command()
        importer.handle(filenames=[], verbosity=1)
        return super().get(request, *args, **kwargs)
