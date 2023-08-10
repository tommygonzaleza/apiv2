# Generated by Django 3.2.20 on 2023-08-05 03:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0058_alter_cohort_available_as_saas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cohortuser',
            name='history_log',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=
                'The cohort user log will save attendancy and information about progress on each class'),
        ),
    ]
