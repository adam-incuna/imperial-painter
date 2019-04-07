from django.conf import settings
from django.views.generic import ListView

from . import models
from .management.commands import import_cards, import_laundry

importers = {
    'import_cards': import_cards,
    'import_laundry': import_laundry,
}


class CardDisplay(ListView):
    model = models.Card
    template_name = 'painter/card_display.html'


class CardDisplayReload(CardDisplay):
    def get(self, request, *args, **kwargs):
        importer = importers[settings.IP_IMPORTER].Command()
        importer.handle(filenames=[], verbosity=1)
        return super().get(request, *args, **kwargs)
