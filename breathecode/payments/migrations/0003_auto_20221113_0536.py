# Generated by Django 3.2.16 on 2022-11-13 05:36

import breathecode.utils.validators.language
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mentorship', '0016_alter_mentorshipbill_status'),
        ('admissions', '0048_academy_main_currency'),
        ('payments', '0002_auto_20221110_0010'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bag',
            old_name='services',
            new_name='service_items',
        ),
        migrations.RenameField(
            model_name='plan',
            old_name='services',
            new_name='service_items',
        ),
        migrations.RenameField(
            model_name='subscription',
            old_name='services',
            new_name='service_items',
        ),
        migrations.RemoveField(
            model_name='consumable',
            name='service',
        ),
        migrations.RemoveField(
            model_name='service',
            name='cohorts',
        ),
        migrations.RemoveField(
            model_name='service',
            name='description',
        ),
        migrations.RemoveField(
            model_name='service',
            name='mentorship_services',
        ),
        migrations.RemoveField(
            model_name='service',
            name='title',
        ),
        migrations.AddField(
            model_name='consumable',
            name='cohort',
            field=models.ForeignKey(blank=True,
                                    default=None,
                                    null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    to='admissions.cohort'),
        ),
        migrations.AddField(
            model_name='consumable',
            name='mentorship_service',
            field=models.ForeignKey(blank=True,
                                    default=None,
                                    null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    to='mentorship.mentorshipservice'),
        ),
        migrations.AddField(
            model_name='consumable',
            name='service_item',
            field=models.ForeignKey(blank=True,
                                    default=None,
                                    null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    to='payments.serviceitem'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='bag',
            field=models.ForeignKey(blank=True,
                                    default=None,
                                    null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    to='payments.bag'),
        ),
        migrations.AddField(
            model_name='plan',
            name='cohorts',
            field=models.ManyToManyField(to='admissions.Cohort'),
        ),
        migrations.AddField(
            model_name='plantranslation',
            name='plan',
            field=models.ForeignKey(blank=True,
                                    default=None,
                                    null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    to='payments.plan'),
        ),
        migrations.AlterField(
            model_name='consumable',
            name='how_many',
            field=models.IntegerField(default=-1),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='amount',
            field=models.FloatField(
                default=0,
                help_text=
                'If amount is 0, transaction will not be sent to stripe or any other payment processor.'),
        ),
        migrations.AlterField(
            model_name='serviceitem',
            name='how_many',
            field=models.IntegerField(default=-1),
        ),
        migrations.CreateModel(
            name='ServiceTranslation',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('lang',
                 models.CharField(max_length=5,
                                  validators=[breathecode.utils.validators.language.validate_language_code])),
                ('title', models.CharField(max_length=60)),
                ('description', models.CharField(max_length=255)),
                ('service',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.service')),
            ],
        ),
        migrations.CreateModel(
            name='Fixture',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('cohort_pattern', models.CharField(blank=True, default=None, max_length=80, null=True)),
                ('mentorship_service_pattern',
                 models.CharField(blank=True, default=None, max_length=80, null=True)),
                ('academy',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admissions.academy')),
                ('service',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.service')),
            ],
        ),
    ]