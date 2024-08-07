# Generated by Django 3.2.12 on 2022-03-04 23:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("admissions", "0031_academy_icon_url"),
        ("monitoring", "0014_csvdownload"),
    ]

    operations = [
        migrations.AlterField(
            model_name="csvdownload",
            name="academy",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="admissions.academy",
            ),
        ),
    ]
