# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-16 20:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('archives', '0001_initial'),
        ('mysessions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LiveExperimentSession',
            fields=[
                ('uid', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(null=True)),
                ('last_activity', models.DateTimeField(null=True)),
                ('last_ping', models.DateTimeField(null=True)),
                ('nowplaying_ping_uid', models.CharField(blank=True, max_length=40, null=True, unique=True)),
                ('keep_alive', models.BooleanField(default=True)),
                ('is_nowplaying', models.BooleanField(default=False)),
                ('alive', models.BooleanField(default=False)),
                ('ua_string', models.CharField(max_length=250, null=True)),
                ('ua_string_pp', models.CharField(max_length=250, null=True)),
                ('ua_browser', models.CharField(max_length=100, null=True)),
                ('ua_browser_version', models.CharField(max_length=10, null=True)),
                ('ua_os', models.CharField(max_length=100, null=True)),
                ('ua_os_version', models.CharField(max_length=10, null=True)),
                ('ua_device', models.CharField(max_length=100, null=True)),
                ('ua_is_mobile', models.NullBooleanField()),
                ('ua_is_tablet', models.NullBooleanField()),
                ('ua_is_touch_capable', models.NullBooleanField()),
                ('ua_is_pc', models.NullBooleanField()),
                ('ua_is_bot', models.NullBooleanField()),
                ('ip_address', models.CharField(max_length=20, null=True)),
                ('city', models.CharField(max_length=100, null=True)),
                ('country_name', models.CharField(max_length=100, null=True)),
                ('country_code', models.CharField(max_length=100, null=True)),
                ('country_code_alt', models.CharField(max_length=100, null=True)),
                ('longitude', models.FloatField(null=True)),
                ('latitude', models.FloatField(null=True)),
                ('platform_info', jsonfield.fields.JSONField(null=True)),
                ('python_info', jsonfield.fields.JSONField(null=True)),
                ('pip_info', jsonfield.fields.JSONField(null=True)),
                ('wilhelm_info', jsonfield.fields.JSONField(null=True)),
                ('experiment_session', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mysessions.ExperimentSession')),
            ],
        ),
        migrations.CreateModel(
            name='SlideToBeLaunchedInfo',
            fields=[
                ('uid', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('ping_uid', models.CharField(max_length=40, null=True)),
                ('slideview_type', models.CharField(choices=[(b'InitialPlaylistSlideView', b'InitialPlaylistSlideView'), (b'LivePlaylistSlideView', b'LivePlaylistSlideView'), (b'PausedPlaylistSlideView', b'PausedPlaylistSlideView'), (b'RepeatPlaylistSlideView', b'RepeatPlaylistSlideView')], max_length=25)),
                ('slideview_kwargs', jsonfield.fields.JSONField(null=True)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='archives.Experiment')),
            ],
        ),
    ]
