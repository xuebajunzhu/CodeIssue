# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-12-06 08:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0012_auto_20191206_0729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deploytask',
            name='deploy_type',
            field=models.PositiveSmallIntegerField(choices=[(1, '全量主机发布'), (2, '自定义主机发布')], default=1, verbose_name='发布类型'),
        ),
        migrations.AlterField(
            model_name='deploytask',
            name='xx',
            field=models.ManyToManyField(through='web.DeployServer', to='web.Server', verbose_name='自定义主机'),
        ),
    ]
