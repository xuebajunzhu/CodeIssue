# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-12-09 04:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0014_auto_20191206_0846'),
    ]

    operations = [
        migrations.CreateModel(
            name='HookScript',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('script', models.TextField(verbose_name='脚本内容')),
                ('env', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.ProjectEnv', verbose_name='环境')),
            ],
        ),
        migrations.RemoveField(
            model_name='deploytask',
            name='xx',
        ),
        migrations.AddField(
            model_name='deploytask',
            name='after_deploy_script',
            field=models.TextField(blank=True, null=True, verbose_name='发布后脚本'),
        ),
        migrations.AddField(
            model_name='deploytask',
            name='after_download_script',
            field=models.TextField(blank=True, null=True, verbose_name='下载后脚本'),
        ),
        migrations.AddField(
            model_name='deploytask',
            name='before_deploy_script',
            field=models.TextField(blank=True, null=True, verbose_name='发布前脚本'),
        ),
        migrations.AddField(
            model_name='deploytask',
            name='before_download_script',
            field=models.TextField(blank=True, null=True, verbose_name='下载前脚本'),
        ),
    ]
