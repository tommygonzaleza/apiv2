from datetime import timedelta
from django.core.management.base import BaseCommand
from breathecode.payments import tasks
from django.db.models.query_utils import Q

from ...models import PlanFinancing, Subscription
from django.utils import timezone


# renew the subscriptions every 1 hours
class Command(BaseCommand):
    help = 'Renew credits'

    def handle(self, *args, **options):
        utc_now = timezone.now()
        statuses = ['CANCELLED', 'DEPRECATED', 'FREE_TRIAL']

        subscriptions = Subscription.objects.filter(valid_until__lte=utc_now + timedelta(days=1))
        plan_financings = PlanFinancing.objects.filter(valid_until__lte=utc_now + timedelta(days=1))

        for status in statuses:
            subscriptions = subscriptions.exclude(status=status)

        statuses.append('FULLY_PAID')

        for status in statuses:
            plan_financings = plan_financings.exclude(status=status)

        for subscription in subscriptions:
            tasks.charge_subscription.delay(subscription.id)

        for plan_financing in plan_financings:
            tasks.charge_plan_financing.delay(plan_financing.id)
