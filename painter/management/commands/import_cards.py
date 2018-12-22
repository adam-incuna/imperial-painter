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

    def parse_header_row(self, worksheet_row, start_index=0, end_index=-1):
        """
        Return a list of parsed header fields.

        Each "field" is a pair of (field_name, is_list). The field_name is suitable for
        use as a variable name; is_list is True if the field is expected to contain a
        list of data, and False otherwise. Any header preceded by an asterisk denotes
        a list field.

        The parser will travel along the row from start_index until it reaches either
        end_index or a blank cell, whichever comes first.
        """
        header_row = worksheet_row[start_index:]

        if (end_index > -1):
            header_row = worksheet_row[start_index:end_index]

        result = []

        for header_cell in header_row:
            # Make it look like a variable name by forcing lowercase and replacing spaces
            # with underscores.
            header = header_cell.value
            if header:
                header = header.lower().replace(' ', '_')

                # Any header preceded by an asterisk denotes a list field.
                if header[0] == '*':
                    result.append((header[1:], True))
                else:
                    result.append((header, False))
            else:
                # If we find a column with a blank header, stop processing new headers.
                break

        return result

    def parse_data_row(self, worksheet_row, headers, start_index=0):
        """
        Turn a row of data from the sheet into a dictionary.

        The keys of the dictionary are given by the corresponding headers.
        Starting at start_index in the worksheet_row, loop until we run out of headers,
        and create a dictionary entry for each cell.

        For headers that represent list fields, parse the cell value into a list
        (separated by newlines).
        """
        result = {}

        for i, header_data in enumerate(headers):
            key = header_data[0]
            is_list = header_data[1]
            value = worksheet_row[start_index + i].value

            # Convert to string to ensure zeros are displayed correctly,
            # and that calling split() doesn't explode.
            # However, if the value is None, skip the string conversion. This means
            # the value shows up correctly as empty, instead of the string "None".
            if value is not None:
                value = str(value)

            # Parse the value as a list if the column was marked as a list type.
            if is_list and value:
                value = value.split('\n')

            result[key] = value

        return result

    def convert_to_python(self, worksheet):
        """
        Turn an openpyxl worksheet into a list of dictionaries.

        Each dictionary represents one card or group of cards that collectively
        form a single game 'entity'. This could be one spell, one attack, a series
        of stat cards for a single unit, and so on.

        The default implementation treats the first
        """
        all_rows = list(worksheet.rows)

        header_row = all_rows[0]
        headers = self.parse_header_row(header_row)

        data_rows = all_rows[1:]
        all_dicts = [self.parse_data_row(data, headers) for data in data_rows]

        return all_dicts

    def convert_to_cards(self, card_data):
        """
        Convert a dictionary into one or more Card objects, returned in a list.

        The dictionary is intended to represent a single entry - convert_to_python
        returns a list of such 'entries'. Often, this will be a single card.

        The basic implementation pops 'name', 'template' and 'quantity' out of
        card_data, then creates one Card with the rest of card_data saved in its
        data field.

        This function is allowed to modify card_data, to avoid copying it.
        """
        # Remove the name, template, and quantity fields from the rest of the data,
        # since they go directly on the Card instance.
        name = card_data.pop('name', None)
        template = card_data.pop('template', None)
        quantity = card_data.pop('quantity', 1)

        # If it has both a name and a template, add it. Otherwise, leave it out.
        # This allows for blank/incomplete/ignored rows to exist in the Excel file.
        if not name or not template:
            return []

        return [Card(
            name=name,
            template_name=self.ensure_extension(template, 'html'),
            quantity=quantity,
            data=card_data,
        )]

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
        for card_data in python_data:
            cards += self.convert_to_cards(card_data)

        # Use bulk_create to store them for an easy performance bump.
        Card.objects.bulk_create(cards)

        # Chirp triumphantly to stdout.
        if verbosity:
            print('{} cards created!'.format(len(cards)))
            print(', '.join([c.name for c in cards]))
