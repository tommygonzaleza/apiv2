# Generated by Django 3.2.9 on 2021-12-22 22:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("admissions", "0029_auto_20211217_0248"),
        ("marketing", "0043_auto_20211111_0010"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeadGenerationApp",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=150, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(max_length=450)),
                (
                    "app_id",
                    models.CharField(
                        help_text="Unique token generated only for this app, can be reset to revoke acceess",
                        max_length=255,
                        unique=True,
                    ),
                ),
                ("hits", models.IntegerField(default=0)),
                (
                    "last_call_log",
                    models.TextField(help_text="Output that was sent to this app on the last call", max_length=450),
                ),
                (
                    "last_call_status",
                    models.CharField(
                        blank=True, choices=[("OK", "Ok"), ("ERROR", "Error")], default=None, max_length=9, null=True
                    ),
                ),
                (
                    "last_call_at",
                    models.DateTimeField(
                        blank=True,
                        default=None,
                        help_text="Timestamp from the last time this app called our API",
                        null=True,
                    ),
                ),
                ("location", models.CharField(blank=True, default=None, max_length=70, null=True)),
                ("language", models.CharField(default="en", max_length=2)),
                ("utm_url", models.URLField(blank=True, default=None, max_length=2000, null=True)),
                ("utm_medium", models.CharField(blank=True, default=None, max_length=70, null=True)),
                ("utm_campaign", models.CharField(blank=True, default=None, max_length=70, null=True)),
                ("utm_source", models.CharField(blank=True, default=None, max_length=70, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("academy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="admissions.academy")),
                ("default_automations", models.ManyToManyField(blank=True, to="marketing.Automation")),
                ("default_tags", models.ManyToManyField(blank=True, to="marketing.Tag")),
            ],
        ),
    ]
