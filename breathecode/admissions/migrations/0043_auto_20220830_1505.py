# Generated by Django 3.2.15 on 2022-08-30 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admissions", "0042_academy_white_labeled"),
    ]

    operations = [
        migrations.AddField(
            model_name="cohort",
            name="history_log",
            field=models.JSONField(
                blank=True,
                default=None,
                help_text="The cohort history will save attendancy and information about progress on each class",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="cohort",
            name="current_day",
            field=models.IntegerField(
                default=1, help_text="Each day the teacher takes attendancy and increases the day in one"
            ),
        ),
    ]
