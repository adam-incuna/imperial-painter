import re

from django.conf import settings
from django.core.management.base import BaseCommand
from openpyxl import load_workbook

from painter.models import Card


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

    def load_all_worksheets(self, filenames, verbosity=0):
        """
        Open a given series of Excel files and return all their worksheets.

        Ignore worksheets whose names start with an @ symbol - these are
        used as metadata.
        """
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

            valid_sheets = [w for w in workbook.worksheets if w.title[0] != '@']

            all_sheets += valid_sheets

        if verbosity:
            titles = [w.title for w in all_sheets]
            titles = ', '.join(titles)
            print('Loading worksheets: {}'.format(titles))

        return all_sheets

    def make_safe_name(self, value):
        """
        Return a form of `value` that's usable as a variable name in a Django template.
        """
        # Replace all spaces with underscores.
        value = value.lower().replace(' ', '_')

        # Remove any non-alphanumeric characters from the name.
        # https://stackoverflow.com/a/2779487
        # https://docs.python.org/3/howto/regex.html#matching-characters
        value = re.sub(r'\W+', '', value)

        return value

    def parse_header_row(self, worksheet_row, start_column=0, width=-1):
        """
        Return a list of parsed header fields.

        Each "field" is a pair of (field_name, is_list). The field_name is suitable for
        use as a variable name; is_list is True if the field is expected to contain a
        list of data, and False otherwise. Any header preceded by an asterisk denotes
        a list field.

        The parser will travel along the row from start_column until it reaches either
        start_column + width or a blank cell, whichever comes first.
        """
        header_row = worksheet_row[start_column:]
        if (width > -1):
            header_row = header_row[:width]

        result = []

        for header_cell in header_row:
            header = header_cell.value
            if header:
                is_list = False

                # Any header preceded by an asterisk denotes a list field.
                if header[0] == '*':
                    header = header[1:]
                    is_list = True

                # Make the header name into a suitable variable name,
                # by forcing lowercase and replacing spaces with underscores.
                header = self.make_safe_name(header)

                result.append((header, is_list))
            else:
                # If we find a column with a blank header, stop processing new headers.
                break

        return result

    def parse_data_row(self, worksheet_row, headers, start_column=0):
        """
        Turn a row of data from the sheet into a dictionary.

        The keys of the dictionary are given by the corresponding headers.
        Starting at start_column in the worksheet_row, loop until we run out of headers,
        and create a dictionary entry for each cell.

        For headers that represent list fields, parse the cell value into a list
        (separated by newlines).

        Return None if the row is completely blank (every cell is empty/None).
        """
        result = {}
        is_empty = True

        for i, header_data in enumerate(headers):
            key = header_data[0]
            is_list = header_data[1]
            value = worksheet_row[start_column + i].value

            # Convert to string to ensure zeros are displayed correctly,
            # and that calling split() doesn't explode.
            # However, if the value is None, skip the string conversion. This means
            # the value shows up correctly as empty, instead of the string "None".
            if value is not None:
                value = str(value)
                is_empty = False

            # Parse the value as a list if the column was marked as a list type.
            if is_list and value:
                value = value.split('\n')

            result[key] = value

        if is_empty:
            return None

        return result

    def parse_table(
        self, worksheet_rows,
        start_row=0, start_column=0, height=-1, width=-1
    ):
        """
        Parse an entire table.

        - The first row (start_row) is taken to be the header row;
          the rest are data rows.
        - First, generate the header row, from start_column to start_column + width
          (or the end of the sheet if width=-1).
        - Then, generate data rows. Iterate from start_row + 1 until start_row +
          height (if specified) or the end of the sheet.

        parse_data_row is called on each data row, and the results are accumulated
        into a list.

        Note that height includes the header row.
        """
        table_rows = worksheet_rows[start_row:]
        if height > -1:
            table_rows = table_rows[:height]

        header_row = table_rows[0]
        headers = self.parse_header_row(header_row, start_column, width)

        data_rows = table_rows[1:]
        parsed_rows = [
            self.parse_data_row(data, headers, start_column)
            for data in data_rows
        ]
        nonempty_rows = [r for r in parsed_rows if r is not None]

        return nonempty_rows

    def convert_to_python(self, worksheet):
        """
        Turn an openpyxl worksheet into a list of dictionaries.

        Each dictionary represents one card or group of cards that collectively
        form a single game 'entity'. This could be one spell, one attack, a series
        of stat cards for a single unit, and so on.

        The base implementation treats the first row as the headers of a table,
        and all the other rows as entries.
        """
        all_rows = list(worksheet.rows)
        return self.parse_table(all_rows)

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
        template_string = card_data.pop('template', None)
        quantity = card_data.pop('quantity', 1)

        # If it has both a name and a template, add it. Otherwise, leave it out.
        # This allows for blank/incomplete/ignored rows to exist in the Excel file.
        if not name or not template_string:
            return []

        # If multiple templates are supplied, create one Card entry for each one
        # (duplicating the card data).
        template_list = template_string.split(',')

        return [
            Card(
                name=name,
                template_name=self.ensure_extension(template.strip(), 'html'),
                quantity=quantity,
                data=card_data,
            )
            for template in template_list
        ]

    def handle(self, *args, **options):
        """DO ALL THE THINGS"""
        verbosity = options['verbosity']

        # The filenames are defined in a setting.
        filenames = settings.IP_DATA_FILES
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
