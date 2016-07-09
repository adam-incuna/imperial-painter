# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('painter', '0002_csvfile'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CsvFile',
            new_name='DataFile',
        ),
    ]
