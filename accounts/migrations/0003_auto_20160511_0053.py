# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-11 00:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20160509_0435'),
    ]

    operations = [
        migrations.AddField(
            model_name='statement',
            name='file_path',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='statement',
            name='file_hash',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='statement',
            name='file_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
