# Generated by Django 3.2.16 on 2022-11-09 23:05

import breathecode.utils.validators.language
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('admissions', '0047_merge_20220924_0611'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mentorship', '0016_alter_mentorshipbill_status'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Consumable',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('unit_type', models.CharField(choices=[('UNIT', 'Unit')], default='UNIT', max_length=10)),
                ('how_many', models.IntegerField(default=0)),
                ('valid_until', models.DateTimeField(blank=True, default=None, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('code', models.CharField(max_length=3)),
                ('name', models.CharField(max_length=20)),
                ('countries',
                 models.ManyToManyField(help_text='Countries that use this currency officially',
                                        related_name='currencies',
                                        to='admissions.Country')),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('amount', models.FloatField(default=0)),
                ('paid_at', models.DateTimeField()),
                ('status',
                 models.CharField(choices=[('FULFILLED', 'Fulfilled'), ('REJECTED', 'Rejected'),
                                           ('PENDING', 'Pending'), ('REFUNDED', 'Refunded'),
                                           ('DISPUTED_AS_FRAUD', 'Disputed as fraud')],
                                  default='PENDING',
                                  max_length=17)),
                ('stripe_id', models.CharField(blank=True, default=None, max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academy',
                 models.ForeignKey(blank=True,
                                   default=None,
                                   null=True,
                                   on_delete=django.db.models.deletion.CASCADE,
                                   to='admissions.academy')),
                ('currency',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.currency')),
                ('user',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('price_per_month', models.FloatField(default=0)),
                ('price_per_quarter', models.FloatField(default=0)),
                ('price_per_half', models.FloatField(default=0)),
                ('price_per_year', models.FloatField(default=0)),
                ('slug', models.CharField(max_length=60, unique=True)),
                ('status',
                 models.CharField(choices=[('DRAFT', 'Draft'), ('VISIBLE', 'Visible'), ('HIDDEN', 'Hidden'),
                                           ('DELETED', 'Deleted')],
                                  default='DRAFT',
                                  max_length=7)),
                ('renew_every', models.IntegerField(default=1)),
                ('renew_every_unit',
                 models.CharField(choices=[('DAY', 'Day'), ('WEEK', 'Week'), ('MONTH', 'Month'),
                                           ('YEAR', 'Year')],
                                  default='MONTH',
                                  max_length=10)),
                ('trial_duration', models.IntegerField(default=1)),
                ('trial_duration_unit',
                 models.CharField(choices=[('DAY', 'Day'), ('WEEK', 'Week'), ('MONTH', 'Month'),
                                           ('YEAR', 'Year')],
                                  default='MONTH',
                                  max_length=10)),
                ('currency',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.currency')),
                ('owner',
                 models.ForeignKey(blank=True,
                                   null=True,
                                   on_delete=django.db.models.deletion.CASCADE,
                                   to='admissions.academy')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PlanTranslation',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('lang',
                 models.CharField(max_length=5,
                                  validators=[breathecode.utils.validators.language.validate_language_code])),
                ('title', models.CharField(max_length=60)),
                ('description', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('price_per_unit', models.FloatField(default=0)),
                ('slug', models.CharField(max_length=60, unique=True)),
                ('title', models.CharField(max_length=60)),
                ('description', models.CharField(max_length=255)),
                ('private', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cohorts', models.ManyToManyField(to='admissions.Cohort')),
                ('currency',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.currency')),
                ('groups', models.ManyToManyField(to='auth.Group')),
                ('mentorship_services', models.ManyToManyField(to='mentorship.MentorshipService')),
                ('owner',
                 models.ForeignKey(blank=True,
                                   null=True,
                                   on_delete=django.db.models.deletion.CASCADE,
                                   to='admissions.academy')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceItem',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('unit_type', models.CharField(choices=[('UNIT', 'Unit')], default='UNIT', max_length=10)),
                ('how_many', models.IntegerField(default=0)),
                ('renew_every', models.IntegerField(default=1)),
                ('renew_every_unit',
                 models.CharField(choices=[('DAY', 'Day'), ('WEEK', 'Week'), ('MONTH', 'Month'),
                                           ('YEAR', 'Year')],
                                  default='MONTH',
                                  max_length=10)),
                ('service',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.service')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('paid_at', models.DateTimeField()),
                ('status',
                 models.CharField(choices=[('FREE_TRIAL', 'Free trial'), ('ACTIVE', 'Active'),
                                           ('CANCELLED', 'Cancelled'), ('DEPRECATED', 'Deprecated'),
                                           ('PAYMENT_ISSUE', 'Payment issue')],
                                  default='ACTIVE',
                                  max_length=13)),
                ('is_cancellable', models.BooleanField(default=True)),
                ('is_refundable', models.BooleanField(default=True)),
                ('is_auto_renew', models.BooleanField(default=True)),
                ('valid_until', models.DateTimeField()),
                ('last_renew', models.DateTimeField()),
                ('renew_credits_at', models.DateTimeField()),
                ('pay_every', models.IntegerField(default=1)),
                ('pay_every_unit',
                 models.CharField(choices=[('DAY', 'Day'), ('WEEK', 'Week'), ('MONTH', 'Month'),
                                           ('YEAR', 'Year')],
                                  default='MONTH',
                                  max_length=10)),
                ('renew_every', models.IntegerField(default=1)),
                ('renew_every_unit',
                 models.CharField(choices=[('DAY', 'Day'), ('WEEK', 'Week'), ('MONTH', 'Month'),
                                           ('YEAR', 'Year')],
                                  default='MONTH',
                                  max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoices', models.ManyToManyField(to='payments.Invoice')),
                ('plans', models.ManyToManyField(to='payments.Plan')),
                ('services', models.ManyToManyField(to='payments.ServiceItem')),
                ('user',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='plan',
            name='services',
            field=models.ManyToManyField(to='payments.ServiceItem'),
        ),
        migrations.CreateModel(
            name='PaymentContact',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=20)),
                ('user',
                 models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                      related_name='payment_contact',
                                      to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FinancialReputation',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('in_4geeks',
                 models.CharField(choices=[('FULFILLED', 'Fulfilled'), ('REJECTED', 'Rejected'),
                                           ('PENDING', 'Pending'), ('REFUNDED', 'Refunded'),
                                           ('DISPUTED_AS_FRAUD', 'Disputed as fraud')],
                                  default='GOOD',
                                  max_length=17)),
                ('in_stripe',
                 models.CharField(choices=[('FULFILLED', 'Fulfilled'), ('REJECTED', 'Rejected'),
                                           ('PENDING', 'Pending'), ('REFUNDED', 'Refunded'),
                                           ('DISPUTED_AS_FRAUD', 'Disputed as fraud')],
                                  default='GOOD',
                                  max_length=17)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user',
                 models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                      related_name='reputation',
                                      to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Credit',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('valid_until', models.DateTimeField(blank=True, default=None, null=True)),
                ('is_free_trial', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.invoice')),
                ('services', models.ManyToManyField(to='payments.Consumable')),
            ],
        ),
        migrations.AddField(
            model_name='consumable',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.service'),
        ),
        migrations.AddField(
            model_name='consumable',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Bag',
            fields=[
                ('id',
                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                     verbose_name='ID')),
                ('amount_per_month', models.FloatField(default=0)),
                ('amount_per_quarter', models.FloatField(default=0)),
                ('amount_per_half', models.FloatField(default=0)),
                ('amount_per_year', models.FloatField(default=0)),
                ('status',
                 models.CharField(choices=[('CHECKING', 'Checking'), ('PAID', 'Paid')],
                                  default='CHECKING',
                                  max_length=8)),
                ('type',
                 models.CharField(choices=[('BAG', 'Bag'), ('PREVIEW', 'Preview')],
                                  default='BAG',
                                  max_length=7)),
                ('chosen_period',
                 models.CharField(choices=[('MONTH', 'Month'), ('QUARTER', 'Quarter'), ('HALF', 'Half'),
                                           ('YEAR', 'Year')],
                                  default='MONTH',
                                  max_length=7)),
                ('is_recurrent', models.BooleanField(default=False)),
                ('was_delivered', models.BooleanField(default=False)),
                ('token', models.CharField(blank=True, db_index=True, default=None, max_length=40,
                                           null=True)),
                ('expires_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academy',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admissions.academy')),
                ('currency',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.currency')),
                ('plans', models.ManyToManyField(to='payments.Plan')),
                ('services', models.ManyToManyField(to='payments.ServiceItem')),
                ('user',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]