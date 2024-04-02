# Generated by Django 3.0.7 on 2020-06-19 19:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0012_auto_20200619_1851'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='automation',
            field=models.ForeignKey(default=None,
                                    help_text='Leads that contain this tag will be asociated to this automation',
                                    null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    to='marketing.Automation'),
        ),
        migrations.AlterField(
            model_name='automation',
            name='status',
            field=models.CharField(choices=[('1', 'Active'), ('2', 'Innactive'), ('0', 'Uknown')],
                                   default='0',
                                   help_text='2 = inactive, 1=active',
                                   max_length=1),
        ),
    ]
