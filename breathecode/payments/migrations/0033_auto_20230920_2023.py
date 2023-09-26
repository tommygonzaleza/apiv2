# Generated by Django 3.2.21 on 2023-09-20 20:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0062_syllabus_is_documentation'),
        ('payments', '0032_auto_20230915_0702'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cohortset',
            name='cohorts',
        ),
        migrations.CreateModel(
            name='CohortSetCohort',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('cohort',
                 models.ForeignKey(help_text='Cohort',
                                   on_delete=django.db.models.deletion.CASCADE,
                                   to='admissions.cohort')),
                ('cohort_set',
                 models.ForeignKey(help_text='Cohort set',
                                   on_delete=django.db.models.deletion.CASCADE,
                                   to='payments.cohortset')),
            ],
        ),
    ]