from painter.models import Card
from .import_cards import Command as BaseImportCommand


class Command(BaseImportCommand):
    help = ('Clears the database of cards, then fills it with the contents of one or' +
            ' more specified XLSX files. Parses a Laundry character sheet,' +
            ' looking for a specific layout.')

    def convert_to_python(self, worksheet):
        """
        Each worksheet in this file represents a single character.

        The sheet contains several tables, in different locations.
        """
        all_rows = list(worksheet.rows)

        identity_table = self.parse_table(
            all_rows, start_row=0, height=2, width=4)
        traits_table = self.parse_table(
            all_rows, start_row=0, start_column=5, height=2, width=4)
        spell_table = self.parse_table(
            all_rows, start_row=0, start_column=10, height=5, width=5)
        stat_table = self.parse_table(
            all_rows, start_row=3, height=9, width=3)
        derived_stat_table = self.parse_table(
            all_rows, start_row=3, start_column=4, height=8, width=2)
        skill_table = self.parse_table(
            all_rows, start_row=15, width=7)

        # Both the identity and traits tables only have a single row.
        identity = identity_table[0]
        traits = traits_table[0]

        # Damage bonuses are converted to dice, using a table.
        # Automate that here and add it to derived_stats.
        bonus = 20  # A neutral amount that causes no damage bonus/penalty
        for stat_row in derived_stat_table:
            if (stat_row['derived_stat'] == 'damage_bonus'):
                bonus = int(stat_row['value'])

                if bonus <= 12:
                    bonus_die = '-1d6'
                elif bonus <= 16:
                    bonus_die = '-1d4'
                elif bonus <= 24:
                    bonus_die = 'None'
                elif bonus <= 32:
                    bonus_die = '+1d4'
                elif bonus <= 40:
                    bonus_die = '+1d6'
                else:
                    bonus_die = '+2d6'

                stat_row['value'] = bonus_die
                break

        # For the skills, we also want to invert the table, but we also need
        # to collapse specialisations into bracketed names. For instance,
        # a table might look like this:
        #    Knowledge
        #        Speciality 1: 9
        #        Speciality 2: 19
        # and we want to combine those into
        #    Knowledge (Speciality 1): 9
        #    Knowledge (Speciality 2): 19
        # Finally, we also want to filter out skills with a value of 1 or less
        # - those are pretty much just visual noise.
        # We can tell what the 'parent' skills are since they have no value,
        # and the 'child' skills because they are indented with a few spaces
        # in the table.
        skills = []
        parent_skill_name = None

        for skill_row in skill_table:
            # Grab the name of the skill, since we'll need it.
            name = skill_row['skill']

            # If this skill is a speciality (we can tell because its name
            # was indented with spaces, so now begins with some underscores),
            # add it to the name of its 'parent'.
            # If it's not a speciality, save it as the next parent_skill_name
            # in case it has specialities of its own.
            if (name[0] == ' '):
                # Remove the indent spaces.
                name = name.lstrip()

                # Filter out the 'Speciality N' example rows.
                if (name.startswith('Speciality')):
                    continue

                name = '{parent} ({speciality})'.format(
                    parent=parent_skill_name,
                    speciality=name
                )
            else:
                parent_skill_name = name

            # If the skill has a value and that value is at least 1, create
            # an entry for it in `skills`.
            value = skill_row['total']
            if (value is not None and int(value) > 2):
                skills.append({
                    'name': name,
                    'value': value,
                })

        # Use some swanky Python 3.5 syntax to merge dictionaries together,
        # putting the identity and trait data on the root level.
        character = {
            **identity,
            **traits,
            'stats': stat_table,
            'derived_stats': derived_stat_table,
            'skills': skills,
            'spells': spell_table,
        }

        return [character]

    def convert_to_cards(self, card_data):
        """
        Convert each character into three cards:
        - Core and derived stats
        - Skills
        - Spells and weapons
        """
        name = card_data.pop('name')
        if not name:
            return []

        cards = [
            Card(
                name=name,
                template_name='stats.html',
                quantity=1,
                data=card_data,
            ),
            Card(
                name=name,
                template_name='skills.html',
                quantity=1,
                data=card_data,
            ),
        ]

        if card_data['spells']:
            cards.append(Card(
                name=name,
                template_name='spells.html',
                quantity=1,
                data=card_data,
            ))

        return cards
