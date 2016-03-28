import tablib
from django.core.management.base import BaseCommand

from painter.models import Card, CsvFile


class Command(BaseCommand):
    help = ('Clears the database of cards, then fills it with the contents of one or' +
            ' more specified CSV files.')

    def add_arguments(self, parser):
        parser.add_argument(
            'filenames',
            nargs='*',
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
        with open(filename, 'r') as csv_file:
            file_contents = csv_file.read()
        return file_contents

    def handle(self, *args, **options):
        # If no filenames are supplied, use the stored ones
        # (then delete them anyway so they get regenerated).
        filenames = options['filenames']
        if not filenames:
            filenames = [cf.name for cf in CsvFile.objects.all()]

        # Clear all existing data.
        CsvFile.objects.all().delete()
        Card.objects.all().delete()

        # Import!
        for filename in filenames:
            filename = self.ensure_extension(filename, 'csv')
            if options['verbosity']:  # pragma: nocover - this is here to make tests quiet
                print("Loading {}".format(filename))

            CsvFile.objects.create(name=filename)
            file_contents = self.open_csv_file(filename)

            # Load the CSV data and ensure it's safe for Python and template use.
            dataset = tablib.Dataset()
            dataset.csv = file_contents
            dataset.headers = self.safe_headers(dataset.headers)
            python_data = dataset.dict

            # Go no further if we don't have any data.
            if not python_data:  # pragma: nocover
                print('No cards were created.')
                return

            # Create the cards!
            for entry in python_data:
                Card.objects.create(
                    name=entry.pop('name'),
                    template_name=self.ensure_extension(entry.pop('template'), 'html'),
                    # The 'name' and 'template_name' have been removed, woo!
                    # We still need to deal with list columns though.
                    data=self.parse_card_data(entry),
                )

    def parse_card_data(self, card_data):
        """
        Parse columns in python_data that contain newlines into lists.

        CSV doesn't support lists natively, so I've added a workaround: any data field
        in your Excel spreadsheet or CSV file can be turned into a list by preceding
        the name of the column with an asterisk. "*Rules Text", for instance.  This will
        affect every cell of the column regardless of its contents.
        """
        for key, value in card_data.items():
            if key.startswith('*'):
                # Add an empty list if the value is empty, just for consistency.
                if not value:
                    list_value = []
                else:
                    list_value = value.split('\n')

                # Remove the original key from the card_data dictionary and replace it
                # with a de-asterisk'd, listified version. Swish.
                card_data.pop(key)
                key_without_asterisk = key[1:]
                card_data[key_without_asterisk] = list_value

        return card_data
