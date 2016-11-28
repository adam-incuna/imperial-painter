from django.core.management.base import BaseCommand
from openpyxl import load_workbook

from painter.models import Card, DataFile


class Command(BaseCommand):
    help = ('Clears the database of cards, then fills it with the contents of one or' +
            ' more specified XLSX files.')

    def add_arguments(self, parser):
        parser.add_argument(
            'filenames',
            nargs='*',
            type=str,
            help='One or more XLSX file names. The extension is optional.',
        )

    def ensure_extension(self, filename, extension):
        """Tag a filename with a given file format if it doesn't have one already."""
        extension = '.' + extension
        if filename.endswith(extension):
            return filename
        return filename + extension

    def get_and_store_filenames(self, **options):
        """
        If no filenames are supplied, use the stored ones.  Otherwise, clear any stored
        filenames and create new ones.
        """
        filenames = options['filenames']

        if not filenames:
            filenames = [df.name for df in DataFile.objects.all()]
        else:
            DataFile.objects.all().delete()
            for filename in filenames:
                DataFile.objects.create(name=filename)

        return filenames

    def load_all_worksheets(self, filenames, verbosity=0):
        """Open a given series of Excel files and return all their worksheets."""
        all_sheets = []

        for filename in filenames:
            filename = self.ensure_extension(filename, 'xlsx')
            if verbosity:
                print("Loading {}".format(filename))

            workbook = load_workbook(
                filename=filename,
                # read_only=True,  # read_only mode causes sharing violations...
                data_only=True,  # Load the values computed by formulae, not the formulae
                keep_vba=False,  # Throw away any VBA scripting
            )
            all_sheets += workbook.worksheets

        return all_sheets

    def convert_to_python(self, worksheet):
        """
        Turn an openpyxl worksheet into a list of dictionaries.

        Each dictionary represents one card.

        We need to do the following:
        - Parse the headers into dict keys we can use safely in a Django template.
        - Figure out which ones are supposed to be lists; any header preceded by an
          asterisk denotes a list field.
        - Convert each row into a dictionary, parsing any list field values
          into lists along the way using `split(\n)`.
        """
        all_rows = list(worksheet.rows)
        header_row = all_rows[0]
        data_rows = all_rows[1:]

        headers = []
        is_list = []
        for header_cell in header_row:
            # Make it look like a variable name by forcing lowercase and replacing spaces
            # with underscores.
            header = header_cell.value
            if header:
                header = header.lower().replace(' ', '_')

                # Any header preceded by an asterisk denotes a list field.
                if header[0] == '*':
                    is_list.append(True)
                    headers.append(header[1:])
                else:
                    is_list.append(False)
                    headers.append(header)
            else:
                # If we find a column with a blank header, stop processing new headers.
                break

        all_dicts = []
        for data in data_rows:
            data_dict = {}

            # Loop along the row and parse the cell values.
            for i, cell in enumerate(data):
                value = cell.value

                # Blank columns can confuse the system (thanks, LibreOffice).
                # We've already stopped taking that data on board thanks to the header
                # code, so just quietly throw out anything that's bigger than our list
                # of headers.
                if i >= len(headers):
                    continue

                if value is not None:
                    # Convert to string to ensure zeros are displayed correctly
                    # and that calling split() doesn't explode.
                    value = str(value)
                    # Parse the value as a list if the column was marked as a list type.
                    if is_list[i] and value:
                        value = value.split('\n')

                # Store the value as None if it was None to begin with, to ensure we get
                # proper empty entries as opposed to a lot of data fields full of the
                # word "None".
                data_dict[headers[i]] = value

            # Save the newly parsed values as an entry in the list of dictionaries.
            all_dicts.append(data_dict)

        return all_dicts

    def handle(self, *args, **options):
        """DO ALL THE THINGS"""
        verbosity = options['verbosity']

        # Get the right filenames and ensure they're in sync with the stored DataFiles
        # (one way or another).
        filenames = self.get_and_store_filenames(**options)
        if not filenames:
            return

        # Clear all card data before we go any further.
        Card.objects.all().delete()

        # Import!
        worksheets = self.load_all_worksheets(filenames, verbosity)
        python_data = []
        for sheet in worksheets:
            python_data += self.convert_to_python(sheet)

        # Stop right here if we don't have any data.
        if not python_data:
            if verbosity:
                print('No cards were created.')
            return

        # Create the card objects.
        cards = []
        for entry in python_data:
            # If it has both a name and a template, add it. Otherwise, leave it out.
            # This allows for blank/incomplete/ignored rows to exist in the Excel file.
            name = entry.pop('name', None)
            template = entry.pop('template', None)
            if not name or not template:
                continue

            cards.append(Card(
                name=name,
                template_name=self.ensure_extension(template, 'html'),
                quantity=entry.pop('quantity', 1) or 1,
                data=entry,
            ))

        # Use bulk_create to store them for an easy performance bump.
        Card.objects.bulk_create(cards)

        # Chirp triumphantly to stdout.
        if verbosity:
            print('{} cards created!'.format(len(cards)))
            print('Data columns: ' + ', '.join(python_data[0].keys()))
            print(', '.join([c.name for c in cards]))
