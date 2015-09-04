import tablib
from django.core.management.base import BaseCommand

from painter.models import Card


class Command(BaseCommand):
    def handle(self, *args, **options):
        dataset = tablib.Dataset()
