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

    def ensure_extension(self, filename, extension):
        """Add '.[extension]' onto the end of filename if it isn't already there."""
        extension = '.' + extension
        if filename.endswith(extension):
            return filename
        return filename + extension

    def safe_headers(self, headers):
        """Replace spaces with underscores and make everything lowercase."""
        return [
            header.lower().replace(' ', '_')
            for header in headers
        ]

    def handle(self, *args, **options):
        Card.objects.all().delete()

        for filename in options['filenames']:
            # Open the CSV file.
            filename = self.ensure_extension(filename, 'csv')
            with open(filename, 'r') as csv_file:
                file_contents = csv_file.read()

            # Load the CSV data and ensure it's safe for Python and template use.
            dataset = tablib.Dataset()
            dataset.csv = file_contents
            dataset.headers = self.safe_headers(dataset.headers)
            python_data = dataset.dict

            # Create the cards!
            for entry in python_data:
                new_card = Card.objects.create(
                    name=entry.pop('name'),
                    template_name=self.ensure_extension(entry.pop('template'), 'html'),
                    data=entry,  # the 'name' and 'template_name' have been removed, woo!
                )
