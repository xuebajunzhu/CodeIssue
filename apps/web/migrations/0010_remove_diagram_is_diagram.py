# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-12-06 04:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0009_diagram_is_diagram'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diagram',
            name='is_diagram',
        ),
    ]
