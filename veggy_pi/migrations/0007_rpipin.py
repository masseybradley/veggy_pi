# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-06-18 07:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('veggy_pi', '0006_auto_20160617_1454'),
    ]

    operations = [
        migrations.CreateModel(
            name='RPiPin',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('veggy_pi.pin',),
        ),
    ]
