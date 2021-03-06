# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-12 23:02
from __future__ import unicode_literals

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('accounts', '0004_auto_20160511_0357'),
    ]

    operations = [
        migrations.RenameField(
            model_name='merchant',
            old_name='regex_list',
            new_name='pattern',
        ),
        migrations.AddField(
            model_name='merchant',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
