# Generated by Django 3.2.16 on 2023-02-22 00:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admissions", "0053_alter_cohort_kickoff_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="cohortuser",
            name="history_log",
            field=models.JSONField(
                blank=True,
                default={},
                help_text="The cohort user log will save attendancy and information about progress on each class",
            ),
        ),
    ]
