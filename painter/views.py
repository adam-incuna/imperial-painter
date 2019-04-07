import importlib

from django.conf import settings
from django.views.generic import ListView

from . import models

# settings.IP_IMPORTER needs to point to a management command.
# There are two default ones:
#  * painter.management.commands.import_cards
#  * painter.management.commands.import_laundry
ip_importer = importlib.import_module(settings.IP_IMPORTER)

class CardDisplay(ListView):
    model = models.Card
    template_name = 'painter/card_display.html'


class CardDisplayReload(CardDisplay):
    def get(self, request, *args, **kwargs):
        importer = ip_importer.Command()
        importer.handle(filenames=[], verbosity=1)
        return super().get(request, *args, **kwargs)
