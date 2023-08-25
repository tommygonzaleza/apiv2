# Generated by Django 3.2.18 on 2023-08-21 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentorship', '0025_alter_calendlyorganization_max_concurrent_sessions'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendlyorganization',
            name='uri',
            field=models.URLField(default='https://calendly.com',
                                  help_text='Automatically collected from calendly API'),
            preserve_default=False,
        ),
    ]
