# Generated by Django 3.2.9 on 2021-12-05 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admissions", "0026_remove_specialtymode_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="cohorttimeslot",
            name="timezone",
            field=models.CharField(default="America/New_York", max_length=50),
        ),
        migrations.AddField(
            model_name="specialtymodetimeslot",
            name="timezone",
            field=models.CharField(default="America/New_York", max_length=50),
        ),
    ]
