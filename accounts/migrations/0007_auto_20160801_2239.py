# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_transaction_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='statement',
            old_name='imported',
            new_name='parsed',
        ),
    ]
