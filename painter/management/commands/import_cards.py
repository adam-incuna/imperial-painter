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

    def open_csv_file(self, filename):  # pragma: nocover - way too much hassle to test
        """Return the contents of a CSV file.  Separated out for testing purposes."""
        filename = self.ensure_extension(filename, 'csv')
        with open(filename, 'r') as csv_file:
            file_contents = csv_file.read()
        return file_contents

    def handle(self, *args, **options):
        Card.objects.all().delete()

        for filename in options['filenames']:
            file_contents = self.open_csv_file(filename)
            print(file_contents)

            # Load the CSV data and ensure it's safe for Python and template use.
            dataset = tablib.Dataset()
            dataset.csv = file_contents
            dataset.headers = self.safe_headers(dataset.headers)
            python_data = dataset.dict

            # Go no further if we don't have any data.
            if not python_data:  # pragma: nocover
                print('No cards were created.')
                return

            # Deal properly with columns that hold lists, which CSV doesn't support.
            self.parse_list_columns(python_data)

            # Create the cards!
            for entry in python_data:
                Card.objects.create(
                    name=entry.pop('name'),
                    template_name=self.ensure_extension(entry.pop('template'), 'html'),
                    data=entry,  # the 'name' and 'template_name' have been removed, woo!
                )


    def parse_list_columns(self, python_data):
        """
        Parse columns in python_data that contain newlines into lists.

        CSV doesn't support lists natively, so I've added a workaround: any data field
        in your Excel spreadsheet or CSV file can be turned into a list by putting
        newlines between the list entries.  For instance, separate abilities in a card's
        rules text box can live in a single column, separated by newlines, and will be
        stored as a list inside imperial-painter.  This means you can iterate over them,
        deal smoothly with different numbers of abilities between different cards, and
        so on.

        We can just use split() to do the actual parsing, but for consistency, everything
        else under the same column name also has to be transmuted into a list.  This
        means one-line and empty entries become singleton and empty lists respectively,
        so you don't have to special-case your template code to avoid things like for
        loops adding a separate block for each character in a one-line string.
        """
        data_keys = list(python_data[0].keys())
        data_keys.remove('name')
        data_keys.remove('template')

        for key in data_keys:
            is_list = False
            for card in python_data:
                if '\n' in card[key]:
                    self.make_list_column(python_data, key)
                    break

    def make_list_column(self, python_data, column_key):
        """
        Helper method for parse_list_columns that turns all the entries in the named
        column into lists.
        """
        for card in python_data:
            if not card[column_key]:
                card[column_key] = []
            else:
                card[column_key] = card[column_key].split('\n')
