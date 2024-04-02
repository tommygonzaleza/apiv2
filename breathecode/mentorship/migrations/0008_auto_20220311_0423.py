# Generated by Django 3.2.12 on 2022-03-11 04:23

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('admissions', '0037_alter_cohort_schedule'),
        ('mentorship', '0007_auto_20220227_1654'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentorshipservice',
            name='max_duration',
            field=models.DurationField(
                default=datetime.timedelta(seconds=7200),
                help_text='Maximum allowed duration or extra time, make it 0 for unlimited meetings'),
        ),
        migrations.AddField(
            model_name='mentorshipservice',
            name='missed_meeting_duration',
            field=models.DurationField(
                default=datetime.timedelta(seconds=600),
                help_text="Duration that will be paid when the mentee doesn't come to the session"),
        ),
        migrations.AddField(
            model_name='mentorshipsession',
            name='accounted_duration',
            field=models.DurationField(blank=True,
                                       default=None,
                                       help_text='The duration that will be paid to the mentor for this session',
                                       null=True),
        ),
        migrations.AddField(
            model_name='mentorshipsession',
            name='status_message',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='mentorshipsession',
            name='status',
            field=models.CharField(
                choices=[('PENDING', 'Pending'), ('STARTED', 'Started'), ('COMPLETED', 'Completed'),
                         ('FAILED', 'Failed'), ('IGNORED', 'Ignored')],
                default='PENDING',
                help_text=
                'Options are: PENDING, STARTED, COMPLETED, FAILED, IGNORED. Ignored sessions will not be billed.',
                max_length=15),
        ),
        migrations.CreateModel(
            name='MentorshipBill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status',
                 models.CharField(choices=[('DUE', 'Due'), ('APPROVED', 'Approved'), ('PAID', 'Paid')],
                                  default='DUE',
                                  max_length=20)),
                ('status_mesage',
                 models.TextField(blank=True,
                                  default=None,
                                  help_text='Any important information about the bill',
                                  null=True)),
                ('total_duration_in_minutes', models.FloatField(default=0)),
                ('total_duration_in_hours', models.FloatField(default=0)),
                ('total_price', models.FloatField(default=0)),
                ('overtime_minutes',
                 models.FloatField(
                     default=0, help_text='Additional time mentorships took based on the expected default duration')),
                ('paid_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academy',
                 models.ForeignKey(default=None,
                                   null=True,
                                   on_delete=django.db.models.deletion.CASCADE,
                                   to='admissions.academy')),
                ('mentor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             to='mentorship.mentorprofile')),
                ('reviewer',
                 models.ForeignKey(default=None,
                                   null=True,
                                   on_delete=django.db.models.deletion.CASCADE,
                                   to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='mentorshipsession',
            name='bill',
            field=models.ForeignKey(blank=True,
                                    default=None,
                                    help_text='If null, it has not been billed by the mentor yet',
                                    null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    to='mentorship.mentorshipbill'),
        ),
    ]
