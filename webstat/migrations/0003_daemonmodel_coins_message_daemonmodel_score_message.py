# Generated by Django 4.1.5 on 2023-02-01 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webstat', '0002_daemonmodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='daemonmodel',
            name='coins_message',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='daemonmodel',
            name='score_message',
            field=models.CharField(blank=True, default='', max_length=300, null=True),
        ),
    ]
