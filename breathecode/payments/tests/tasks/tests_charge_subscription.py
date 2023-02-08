"""
Test /answer
"""
import logging
import random
from unittest.mock import MagicMock, call, patch

from django.utils import timezone
from breathecode.payments import tasks

from ...tasks import charge_subscription
from breathecode.notify import actions as notify_actions
from ..mixins import PaymentsTestCase
from dateutil.relativedelta import relativedelta
from mixer.backend.django import mixer

UTC_NOW = timezone.now()


def subscription_item(data={}):
    return {
        'id': 1,
        'is_refundable': True,
        'paid_at': UTC_NOW,
        'pay_every': 1,
        'pay_every_unit': 'MONTH',
        'status': 'ACTIVE',
        'user_id': 1,
        'valid_until': UTC_NOW,
        **data,
    }


def bag_item(data={}):
    return {
        'id': 1,
        'amount_per_month': 0.0,
        'amount_per_quarter': 0.0,
        'amount_per_half': 0.0,
        'amount_per_year': 0.0,
        'currency_id': 0,
        'status': 'CHECKING',
        'type': 'CHARGE',
        'chosen_period': 'NO_SET',
        'how_many_installments': 0,
        'academy_id': 0,
        'user_id': 0,
        'is_recurrent': False,
        'was_delivered': False,
        'token': None,
        'expires_at': None,
        **data,
    }


def invoice_item(data={}):
    return {
        'academy_id': 0,
        'amount': 0.0,
        'bag_id': 2,
        'currency_id': 2,
        'id': 0,
        'paid_at': None,
        'status': 'PENDING',
        'stripe_id': None,
        'user_id': 0,
        'refund_stripe_id': None,
        'refunded_at': None,
        **data,
    }


def fake_stripe_pay(**kwargs):

    def wrapper(user, bag, amount: int, currency='usd', description=''):
        return mixer.blend('payments.Invoice', user=user, bag=bag, **kwargs)

    return wrapper


def calculate_relative_delta(unit: float, unit_type: str):
    delta_args = {}
    if unit_type == 'DAY':
        delta_args['days'] = unit

    elif unit_type == 'WEEK':
        delta_args['weeks'] = unit

    elif unit_type == 'MONTH':
        delta_args['months'] = unit

    elif unit_type == 'YEAR':
        delta_args['years'] = unit

    return relativedelta(**delta_args)


#FIXME: create_v2 fail in this test file
class PaymentsTestSuite(PaymentsTestCase):
    """
    🔽🔽🔽 Subscription not found
    """

    @patch('logging.Logger.info', MagicMock())
    @patch('logging.Logger.error', MagicMock())
    def test_subscription_not_found(self):
        charge_subscription.delay(1)

        self.assertEqual(self.bc.database.list_of('admissions.Cohort'), [])

        self.assertEqual(logging.Logger.info.call_args_list, [
            call('Starting charge_subscription for subscription 1'),
        ])
        self.assertEqual(logging.Logger.error.call_args_list, [call('Subscription with id 1 not found')])

        self.assertEqual(self.bc.database.list_of('payments.Bag'), [])
        self.assertEqual(self.bc.database.list_of('payments.Invoice'), [])
        self.assertEqual(self.bc.database.list_of('payments.Subscription'), [])

    """
    🔽🔽🔽 Subscription with zero Invoice
    """

    @patch('logging.Logger.info', MagicMock())
    @patch('logging.Logger.error', MagicMock())
    @patch('breathecode.notify.actions.send_email_message', MagicMock())
    def test_subscription_without_invoices(self):
        model = self.bc.database.create_v2(subscription=1)

        # remove prints from mixer
        logging.Logger.info.call_args_list = []
        logging.Logger.error.call_args_list = []

        charge_subscription.delay(1)

        self.assertEqual(self.bc.database.list_of('admissions.Cohort'), [])

        self.assertEqual(logging.Logger.info.call_args_list, [
            call('Starting charge_subscription for subscription 1'),
        ])
        self.assertEqual(logging.Logger.error.call_args_list, [
            call('Error getting bag from subscription 1: subscription-has-no-invoices'),
        ])

        self.assertEqual(self.bc.database.list_of('payments.Bag'), [])
        self.assertEqual(self.bc.database.list_of('payments.Invoice'), [])

        self.assertEqual(
            self.bc.database.list_of('payments.Subscription'),
            [
                {
                    **self.bc.format.to_dict(model.subscription),
                    # 'status': 'PAYMENT_ISSUE',,
                    'status': 'ERROR',
                    'status_message': 'subscription-has-no-invoices',
                },
            ])
        self.assertEqual(notify_actions.send_email_message.call_args_list, [])

    """
    🔽🔽🔽 Subscription process to charge
    """

    @patch('logging.Logger.info', MagicMock())
    @patch('logging.Logger.error', MagicMock())
    @patch('breathecode.notify.actions.send_email_message', MagicMock())
    @patch('breathecode.payments.tasks.renew_subscription_consumables.delay', MagicMock())
    @patch('mixer.main.LOGGER.info', MagicMock())
    @patch('django.utils.timezone.now', MagicMock(return_value=UTC_NOW))
    def test_subscription_process_to_charge(self):
        unit = random.choice([1, 3, 6, 12])
        unit_type = 'MONTH'
        subscription = {
            'pay_every': unit,
            'pay_every_unit': unit_type,
        }
        model = self.bc.database.create(subscription=subscription, invoice=1)

        with patch('breathecode.payments.services.stripe.Stripe.pay',
                   MagicMock(side_effect=fake_stripe_pay(paid_at=UTC_NOW))):
            # remove prints from mixer
            logging.Logger.info.call_args_list = []
            logging.Logger.error.call_args_list = []

            charge_subscription.delay(1)

        self.assertEqual(self.bc.database.list_of('admissions.Cohort'), [])

        self.assertEqual(logging.Logger.info.call_args_list, [
            call('Starting charge_subscription for subscription 1'),
        ])
        self.assertEqual(logging.Logger.error.call_args_list, [])

        self.assertEqual(self.bc.database.list_of('payments.Bag'), [
            self.bc.format.to_dict(model.bag),
            bag_item({
                'academy_id': 1,
                'currency_id': 1,
                'id': 2,
                'is_recurrent': True,
                'status': 'RENEWAL',
                'user_id': 1,
            }),
        ])
        self.assertEqual(self.bc.database.list_of('payments.Invoice'), [
            self.bc.format.to_dict(model.invoice),
            invoice_item({
                'academy_id': 2,
                'id': 2,
                'user_id': 1,
                'paid_at': UTC_NOW,
            }),
        ])

        self.assertEqual(self.bc.database.list_of('payments.Subscription'), [
            {
                **self.bc.format.to_dict(model.subscription),
                'status': 'ACTIVE',
                'paid_at': UTC_NOW,
                'next_payment_at': UTC_NOW + calculate_relative_delta(unit, unit_type),
            },
        ])
        self.assertEqual(notify_actions.send_email_message.call_args_list, [
            call(
                'message', model.user.email, {
                    'SUBJECT': 'Your 4Geeks subscription was successfully renewed',
                    'MESSAGE': 'The amount was $0.0',
                    'BUTTON': 'See the invoice',
                    'LINK': '/subscription/1'
                })
        ])

    """
    🔽🔽🔽 Subscription error when try to charge
    """

    @patch('logging.Logger.info', MagicMock())
    @patch('logging.Logger.error', MagicMock())
    @patch('breathecode.notify.actions.send_email_message', MagicMock())
    @patch('breathecode.payments.tasks.renew_subscription_consumables.delay', MagicMock())
    @patch('mixer.main.LOGGER.info', MagicMock())
    @patch('django.utils.timezone.now', MagicMock(return_value=UTC_NOW))
    def test_subscription_error_when_try_to_charge(self):
        unit = random.choice([1, 3, 6, 12])
        unit_type = 'MONTH'
        subscription = {
            'pay_every': unit,
            'pay_every_unit': unit_type,
        }
        model = self.bc.database.create(subscription=subscription, invoice=1)

        with patch('breathecode.payments.services.stripe.Stripe.pay',
                   MagicMock(side_effect=Exception('fake error'))):
            # remove prints from mixer
            logging.Logger.info.call_args_list = []
            logging.Logger.error.call_args_list = []

            charge_subscription.delay(1)

        self.assertEqual(self.bc.database.list_of('admissions.Cohort'), [])

        self.assertEqual(logging.Logger.info.call_args_list, [
            call('Starting charge_subscription for subscription 1'),
        ])
        self.assertEqual(logging.Logger.error.call_args_list, [])

        self.assertEqual(self.bc.database.list_of('payments.Bag'), [
            self.bc.format.to_dict(model.bag),
        ])
        self.assertEqual(self.bc.database.list_of('payments.Invoice'), [
            self.bc.format.to_dict(model.invoice),
        ])

        self.assertEqual(self.bc.database.list_of('payments.Subscription'), [
            {
                **self.bc.format.to_dict(model.subscription),
                'status': 'PAYMENT_ISSUE',
            },
        ])
        self.assertEqual(notify_actions.send_email_message.call_args_list, [
            call(
                'message', model.user.email, {
                    'SUBJECT': 'Your 4Geeks subscription could not be renewed',
                    'MESSAGE': 'Please update your payment methods',
                    'BUTTON': 'Please update your payment methods',
                    'LINK': '/subscription/1'
                })
        ])

    """
    🔽🔽🔽 Subscription is over
    """

    @patch('logging.Logger.info', MagicMock())
    @patch('logging.Logger.error', MagicMock())
    @patch('breathecode.notify.actions.send_email_message', MagicMock())
    @patch('breathecode.payments.tasks.renew_subscription_consumables.delay', MagicMock())
    @patch('mixer.main.LOGGER.info', MagicMock())
    @patch('django.utils.timezone.now', MagicMock(return_value=UTC_NOW))
    def test_subscription_is_over(self):
        unit = random.choice([1, 3, 6, 12])
        unit_type = 'MONTH'
        subscription = {
            'pay_every': unit,
            'pay_every_unit': unit_type,
            'valid_until': UTC_NOW - relativedelta(seconds=1),
        }
        model = self.bc.database.create(subscription=subscription, invoice=1)

        with patch('breathecode.payments.services.stripe.Stripe.pay',
                   MagicMock(side_effect=Exception('fake error'))):
            # remove prints from mixer
            logging.Logger.info.call_args_list = []
            logging.Logger.error.call_args_list = []

            charge_subscription.delay(1)

        self.assertEqual(self.bc.database.list_of('admissions.Cohort'), [])

        self.assertEqual(logging.Logger.info.call_args_list, [
            call('Starting charge_subscription for subscription 1'),
        ])
        self.assertEqual(logging.Logger.error.call_args_list, [call('The subscription 1 is over')])

        self.assertEqual(self.bc.database.list_of('payments.Bag'), [
            self.bc.format.to_dict(model.bag),
        ])
        self.assertEqual(self.bc.database.list_of('payments.Invoice'), [
            self.bc.format.to_dict(model.invoice),
        ])

        self.assertEqual(self.bc.database.list_of('payments.Subscription'), [
            {
                **self.bc.format.to_dict(model.subscription),
            },
        ])
        self.assertEqual(notify_actions.send_email_message.call_args_list, [])
