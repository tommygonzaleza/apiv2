# Generated by Django 3.1 on 2020-08-06 04:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("feedback", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="answer",
            old_name="enity_type",
            new_name="entity_type",
        ),
    ]
