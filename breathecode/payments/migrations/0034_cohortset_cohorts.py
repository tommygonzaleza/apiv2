# Generated by Django 3.2.21 on 2023-09-20 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0062_syllabus_is_documentation'),
        ('payments', '0033_auto_20230920_2023'),
    ]

    operations = [
        migrations.AddField(
            model_name='cohortset',
            name='cohorts',
            field=models.ManyToManyField(blank=True,
                                         through='payments.CohortSetCohort',
                                         to='admissions.Cohort'),
        ),
    ]