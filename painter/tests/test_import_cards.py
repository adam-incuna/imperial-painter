from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from painter.management.commands.import_cards import Command
from painter.models import Card, CsvFile


class TestImportCards(TestCase):
    def load_csv(self, csv_data, filenames=['nonexistent_file.csv']):
        """
        Generate a mock CSV file, call the command to load it, and cache the resulting
        data locally rather than hitting the database every time we need it.
        """
        csv_file = str(csv_data)

        with mock.patch.object(Command, 'open_csv_file', return_value=csv_file):
            # We generally have to supply a file, but it will be ignored since we're
            # mocking out the open_csv_file method.
            call_command('import_cards', *filenames, verbosity=0)

        return {card.name: card for card in Card.objects.all()}

    def test_csv_columns(self):
        """
        The safe_headers method ensures our columns are consistently lowercase and
        using underscores instead of spaces.  All the CSV headers are carried through.
        """
        csv_data = 'name,template,Card Rules\n'
        csv_data += 'a_card,a_template.html,some_data\n'
        cards = self.load_csv(csv_data)

        a_card = cards['a_card']
        self.assertEqual(a_card.template_name, 'a_template.html')
        self.assertEqual(list(a_card.data.keys()), ['card_rules'])

    def test_template_name_fixing(self):
        """All templates end in .html after parsing."""
        csv_data = 'name,template,Card Rules\n'
        csv_data += 'no_html_extension,test,\n'
        cards = self.load_csv(csv_data)

        self.assertEqual(cards['no_html_extension'].template_name, 'test.html')

    def test_list_columns(self):
        """
        A column whose name begins with an asterisk is turned into a list.
        """
        csv_data = 'name,template,*Card Rules\n'
        csv_data += 'non_newlined_rules,test,one_line\n'
        csv_data += 'newlined_rules,test,"new\nline"\n'
        csv_data += 'empty_rules,test,\n'
        cards = self.load_csv(csv_data)

        self.assertEqual(
            cards['non_newlined_rules'].data,
            {'card_rules': ['one_line']}
        )
        self.assertEqual(
            cards['newlined_rules'].data,
            {'card_rules': ['new', 'line']}
        )
        self.assertEqual(
            cards['empty_rules'].data,
            {'card_rules': []}
        )

    def test_csv_file_storage(self):
        """
        A CSV file that's been loaded from is stored, and reused if you pass no filenames,
        or overwritten otherwise.
        """
        csv_data = 'name,template,Card Rules\n'
        csv_data += 'a_card,a_template,some_rules\n'

        # Load data from one file.
        old_cards = self.load_csv(csv_data, filenames=['nonexistent_file.csv'])
        self.assertEqual(CsvFile.objects.count(), 1)
        self.assertEqual(CsvFile.objects.get().name, 'nonexistent_file.csv')
        self.assertEqual(len(old_cards), 1)

        # Load data from a different file and check that it overwrites the CsvFile
        # recorded by the previous.
        new_cards = self.load_csv(csv_data, filenames=['different_file.csv'])
        self.assertEqual(CsvFile.objects.count(), 1)
        self.assertEqual(CsvFile.objects.get().name, 'different_file.csv')
        self.assertEqual(len(new_cards), 1)

        # Load data from no supplied files and check that the previous remaining CsvFile
        # record is used and not removed.
        other_new_cards = self.load_csv(csv_data, filenames=[])
        self.assertEqual(CsvFile.objects.count(), 1)
        self.assertEqual(CsvFile.objects.get().name, 'different_file.csv')
        self.assertEqual(len(other_new_cards), 1)
