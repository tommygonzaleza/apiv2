# Generated by Django 3.2.7 on 2021-11-10 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentorship', '0002_auto_20211109_2203'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentorshipservice',
            name='language',
            field=models.CharField(default='en', max_length=2),
        ),
        migrations.AlterField(
            model_name='mentorshipsession',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')],
                                   default='PENDING',
                                   help_text='Options are: PENDING, COMPLETED, FAILED',
                                   max_length=15),
        ),
    ]
