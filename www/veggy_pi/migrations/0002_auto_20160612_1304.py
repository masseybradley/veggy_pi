# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-06-12 13:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('veggy_pi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configurationoption',
            name='option_label',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]