# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('painter', '0003_rename_csvfile_to_datafile'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='card',
            options={'ordering': ['pk']},
        ),
    ]
