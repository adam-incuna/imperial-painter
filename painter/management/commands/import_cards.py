import tablib
from django.core.management.base import BaseCommand

from painter.models import Card


class Command(BaseCommand):
    help = ('Clears the database of cards, then fills it with the contents of one or' +
            ' more specified CSV files.')

    def add_arguments(self, parser):
        parser.add_argument(
            'filenames',
            nargs='+',
            type=str,
            help='One or more CSV file names. The extension is optional.',
        )

    def ensure_csv_extension(self, filename):
        """Add '.csv' onto the end of filename if it isn't already there."""
        if filename.endswith('.csv'):
            return filename
        return filename + '.csv'

    def handle(self, *args, **options):
        dataset = tablib.Dataset()
        for filename in options['filenames']:
            filename = self.ensure_csv_extension(filename)
            print(filename)
