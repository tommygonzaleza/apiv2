import random
import re
from datetime import UTC, timedelta
from typing import Any
from unittest.mock import MagicMock, call, patch

import capyc.pytest as capy
import pytest
from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

import breathecode.activity.tasks as activity_tasks
from breathecode.payments.tests.mixins.payments_test_case import PaymentsTestCase
from breathecode.tests.mixins.breathecode_mixin.breathecode import Breathecode


def queryset_with_pks(query: Any, pks: list[int]) -> None:
    """
    Check if the queryset have the following primary keys.

    Usage:

    ```py
    from breathecode.admissions.models import Cohort, Academy

    self.bc.database.create(cohort=1)

    collection = []
    queryset = Cohort.objects.filter()

    # pass because the QuerySet has the primary keys 1
    self.bc.check.queryset_with_pks(queryset, [1])  # 🟢

    # fail because the QuerySet has the primary keys 1 but the second argument is empty
    self.bc.check.queryset_with_pks(queryset, [])  # 🔴
    ```
    """

    assert isinstance(query, QuerySet), "The first argument is not a QuerySet"

    assert [x.pk for x in query] == pks


UTC_NOW = timezone.now()


def format_user_setting(data={}):
    return {
        "id": 1,
        "user_id": 1,
        "main_currency_id": None,
        "lang": "en",
        **data,
    }


def financing_option_serializer(financing_option, currency, data={}):
    return {
        "currency": {
            "code": currency.code,
            "name": currency.name,
        },
        "how_many_months": financing_option.how_many_months,
        "monthly_price": financing_option.monthly_price,
        "pricing_ratio_exceptions": financing_option.pricing_ratio_exceptions,
    }


def plan_serializer(plan, service_items, service, cohorts=[], financing_options=[], currency=None, data={}):
    return {
        "service_items": [service_item_serializer(service_item, service, cohorts) for service_item in service_items],
        "financing_options": [
            financing_option_serializer(financing_option, currency) for financing_option in financing_options
        ],
        "slug": plan.slug,
        "status": plan.status,
        "time_of_life": plan.time_of_life,
        "time_of_life_unit": plan.time_of_life_unit,
        "trial_duration": plan.trial_duration,
        "trial_duration_unit": plan.trial_duration_unit,
        "has_available_cohorts": bool(plan.cohort_set),
        **data,
    }


def service_serializer(service, cohorts=[], data={}):
    return {
        "groups": [],
        "private": service.private,
        "slug": service.slug,
        "title": service.title,
        "icon_url": service.icon_url,
        **data,
    }


def service_item_serializer(service_item, service, cohorts=[], data={}):
    return {
        "how_many": service_item.how_many,
        "unit_type": service_item.unit_type,
        "sort_priority": service_item.sort_priority,
        "service": service_serializer(service, cohorts),
        **data,
    }


def to_iso(date):
    return re.sub(r"\+00:00$", "Z", date.replace(tzinfo=UTC).isoformat())


def format_coupon(coupon, data={}):
    return {
        "auto": coupon.auto,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "expires_at": to_iso(coupon.expires_at) if coupon.expires_at else None,
        "offered_at": to_iso(coupon.offered_at) if coupon.offered_at else None,
        "referral_type": coupon.referral_type,
        "referral_value": coupon.referral_value,
        "slug": coupon.slug,
        **data,
    }


def get_serializer(
    bag,
    plans=[],
    plan_service_items=[],
    service_items=[],
    service=None,
    cohorts=[],
    financing_options=[],
    currency=None,
    coupons=[],
    data={},
):
    return {
        "id": bag.id,
        "amount_per_month": bag.amount_per_month,
        "amount_per_quarter": bag.amount_per_quarter,
        "amount_per_half": bag.amount_per_half,
        "amount_per_year": bag.amount_per_year,
        "expires_at": bag.expires_at,
        "is_recurrent": bag.is_recurrent,
        "plans": [
            plan_serializer(plan, plan_service_items, service, cohorts, financing_options, currency) for plan in plans
        ],
        "service_items": [service_item_serializer(service_item, service, cohorts) for service_item in service_items],
        "status": bag.status,
        "token": bag.token,
        "type": bag.type,
        "was_delivered": bag.was_delivered,
        "coupons": [format_coupon(x) for x in coupons],
        **data,
    }


@pytest.fixture(autouse=True)
def setup(db, monkeypatch, set_datetime):
    monkeypatch.setattr(activity_tasks.add_activity, "delay", MagicMock())
    set_datetime(UTC_NOW)
    yield


class SignalTestSuite(PaymentsTestCase):
    """
    🔽🔽🔽 GET without auth
    """

    def test__without_auth(self):
        url = reverse_lazy("payments:checking")
        response = self.client.put(url)

        json = response.json()
        expected = {"detail": "Authentication credentials were not provided.", "status_code": 401}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(self.bc.database.list_of("payments.Bag"), [])
        self.assertEqual(self.bc.database.list_of("authenticate.UserSetting"), [])
        self.bc.check.calls(activity_tasks.add_activity.delay.call_args_list, [])

    """
    🔽🔽🔽 Get with zero Bag
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__without_bag(self):
        model = self.bc.database.create(user=1)
        self.client.force_authenticate(model.user)

        url = reverse_lazy("payments:checking")
        response = self.client.put(url)
        self.client.force_authenticate(model.user)

        json = response.json()
        expected = {"detail": "not-found", "status_code": 404}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(self.bc.database.list_of("payments.Bag"), [])
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting({"lang": "en"}),
            ],
        )
        self.bc.check.calls(activity_tasks.add_activity.delay.call_args_list, [])

    """
    🔽🔽🔽 Get with one Bag, type is BAG
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag(self):
        bag = {
            "status": "CHECKING",
            "type": "BAG",
        }

        cases = [{}, {"type": "BAG"}]
        for case in cases:
            model = self.bc.database.create(user=1, bag=bag)
            self.client.force_authenticate(model.user)

            url = reverse_lazy("payments:checking")

            token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
            with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
                response = self.client.put(url, data=case, format="json")

            json = response.json()
            expected = get_serializer(
                model.bag,
                data={
                    "amount_per_month": 0.0,
                    "amount_per_quarter": 0.0,
                    "amount_per_half": 0.0,
                    "amount_per_year": 0.0,
                    "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                    "token": token,
                    "is_recurrent": False,
                },
            )

            self.assertEqual(json, expected)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.assertEqual(
                self.bc.database.list_of("payments.Bag"),
                [
                    {
                        **self.bc.format.to_dict(model.bag),
                        "amount_per_month": 0.0,
                        "amount_per_quarter": 0.0,
                        "amount_per_half": 0.0,
                        "amount_per_year": 0.0,
                        "expires_at": UTC_NOW + timedelta(minutes=60),
                        "token": token,
                        "is_recurrent": False,
                        "currency_id": 1,
                    },
                ],
            )
            self.assertEqual(
                self.bc.database.list_of("authenticate.UserSetting"),
                [
                    format_user_setting(
                        {
                            "lang": "en",
                            "id": model.user.id,
                            "user_id": model.user.id,
                        }
                    ),
                ],
            )

            # teardown
            self.bc.database.delete("payments.Bag", model.bag.id)
            self.bc.database.delete("authenticate.UserSetting", model.bag.id)
            self.bc.check.calls(
                activity_tasks.add_activity.delay.call_args_list,
                [
                    call(model.user.id, "bag_created", related_type="payments.Bag", related_id=model.user.id),
                ],
            )

            activity_tasks.add_activity.delay.call_args_list = []

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing nothing
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_nothing(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
        }

        model = self.bc.database.create(user=1, bag=bag)
        self.client.force_authenticate(model.user)

        url = reverse_lazy("payments:checking")
        response = self.client.put(url)

        json = response.json()
        expected = {"detail": "not-found", "status_code": 404}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(self.bc.database.list_of("payments.Bag"), [self.bc.format.to_dict(model.bag)])
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
        }

        model = self.bc.database.create(user=1, bag=bag, academy=1, currency=1)
        self.client.force_authenticate(model.user)

        url = reverse_lazy("payments:checking")
        data = {"academy": 1, "type": "PREVIEW"}

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = get_serializer(
            model.bag,
            data={
                "amount_per_month": 0.0,
                "amount_per_quarter": 0.0,
                "amount_per_half": 0.0,
                "amount_per_year": 0.0,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": 0.0,
                    "amount_per_quarter": 0.0,
                    "amount_per_half": 0.0,
                    "amount_per_year": 0.0,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan that not found
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__service_item_not_is_object(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
        }

        model = self.bc.database.create(user=1, bag=bag, academy=1, currency=1)
        self.client.force_authenticate(model.user)

        url = reverse_lazy("payments:checking")
        data = {"academy": 1, "type": "PREVIEW", "plans": [1], "service_items": [1]}

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = {"detail": "service-item-not-object", "status_code": 400}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(self.bc.database.list_of("payments.Bag"), [self.bc.format.to_dict(model.bag)])
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan that not found
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__service_item_object_malformed(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
        }

        model = self.bc.database.create(user=1, bag=bag, academy=1, currency=1)
        self.client.force_authenticate(model.user)

        url = reverse_lazy("payments:checking")
        data = {"academy": 1, "type": "PREVIEW", "plans": [1], "service_items": [{}]}

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = {"detail": "service-item-malformed", "status_code": 400}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(self.bc.database.list_of("payments.Bag"), [self.bc.format.to_dict(model.bag)])
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan that not found
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_not_found(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
        }

        model = self.bc.database.create(user=1, bag=bag, academy=1, currency=1)
        self.client.force_authenticate(model.user)

        url = reverse_lazy("payments:checking")
        data = {"academy": 1, "type": "PREVIEW", "plans": [1], "service_items": [{"how_many": 1, "service": 1}]}

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = {"detail": "some-items-not-found", "status_code": 404}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(self.bc.database.list_of("payments.Bag"), [self.bc.format.to_dict(model.bag)])
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    without the Currency
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__academy_without_the_currency(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        academy = {"main_currency": None}
        plan = {"is_renewable": False}

        model = self.bc.database.create(user=1, bag=bag, service_item=1, plan=plan, academy=academy)
        self.client.force_authenticate(model.user)

        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [])

        url = reverse_lazy("payments:checking")
        data = {"academy": 1, "type": "PREVIEW", "plans": [1], "service_items": [{"how_many": 1, "service": 1}]}

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = {"detail": "not-found", "status_code": 404}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(self.bc.database.list_of("payments.Bag"), [self.bc.format.to_dict(model.bag)])
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__with_the_correct_currency__with_service_item(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": random.random() * 100,
            "price_per_quarter": random.random() * 100,
            "price_per_half": random.random() * 100,
            "price_per_year": random.random() * 100,
            "is_renewable": True,
            "time_of_life": 0,
            "time_of_life_unit": None,
        }

        service = {
            # "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
            "service_items": [{"how_many": how_many2, "service": 1}],
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()
        expected = {"detail": "service-item-not-valid", "status_code": 400}

        assert json == expected
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__with_the_correct_currency__without_service_item(
        self,
    ):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": random.random() * 100,
            "price_per_quarter": random.random() * 100,
            "price_per_half": random.random() * 100,
            "price_per_year": random.random() * 100,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": 0,
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        price_per_month = model.plan.price_per_month
        price_per_quarter = model.plan.price_per_quarter
        price_per_half = model.plan.price_per_half
        price_per_year = model.plan.price_per_year
        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [model.cohort],
            [model.financing_option],
            model.currency,
            data={
                "amount_per_month": price_per_month,
                "amount_per_quarter": price_per_quarter,
                "amount_per_half": price_per_half,
                "amount_per_year": price_per_year,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": price_per_month,
                    "amount_per_quarter": price_per_quarter,
                    "amount_per_half": price_per_half,
                    "amount_per_year": price_per_year,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price, Plan with trial_duration
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__taking_free_trial(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": random.random() * 100,
            "price_per_quarter": random.random() * 100,
            "price_per_half": random.random() * 100,
            "price_per_year": random.random() * 100,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [model.cohort],
            [model.financing_option],
            model.currency,
            data={
                "amount_per_month": 0,
                "amount_per_quarter": 0,
                "amount_per_half": 0,
                "amount_per_year": 0,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": False,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": 0,
                    "amount_per_quarter": 0,
                    "amount_per_half": 0,
                    "amount_per_year": 0,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": False,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price, Plan with trial_duration
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__taking_free_plan__not_renewable(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": 0,
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [model.cohort],
            [],
            model.currency,
            data={
                "amount_per_month": 0,
                "amount_per_quarter": 0,
                "amount_per_half": 0,
                "amount_per_year": 0,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": 0,
                    "amount_per_quarter": 0,
                    "amount_per_half": 0,
                    "amount_per_year": 0,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__taking_free_plan__renewable(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "is_renewable": True,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": 0,
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [model.cohort],
            [],
            model.currency,
            data={
                "amount_per_month": 0,
                "amount_per_quarter": 0,
                "amount_per_half": 0,
                "amount_per_year": 0,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": 0,
                    "amount_per_quarter": 0,
                    "amount_per_half": 0,
                    "amount_per_year": 0,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price, Plan with trial_duration and Subscription
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__free_trial_already_taken(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": random.random() * 100,
            "price_per_quarter": random.random() * 100,
            "price_per_half": random.random() * 100,
            "price_per_year": random.random() * 100,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            subscription=subscription,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        price_per_month = model.plan.price_per_month
        price_per_quarter = model.plan.price_per_quarter
        price_per_half = model.plan.price_per_half
        price_per_year = model.plan.price_per_year
        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [model.cohort],
            [model.financing_option],
            model.currency,
            data={
                "amount_per_month": price_per_month,
                "amount_per_quarter": price_per_quarter,
                "amount_per_half": price_per_half,
                "amount_per_year": price_per_year,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": price_per_month,
                    "amount_per_quarter": price_per_quarter,
                    "amount_per_half": price_per_half,
                    "amount_per_year": price_per_year,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price, Plan with trial_duration and price et 0 and Subscription
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__free_trial_already_taken__amount_is_0(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": 0,
            "price_per_quarter": 0,
            "price_per_half": 0,
            "price_per_year": 0,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            subscription=subscription,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = {"detail": "free-trial-already-bought", "status_code": 400}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price, Plan with trial_duration and price et 0, Subscription and
    FinancingOption
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__free_trial_already_taken__with_financing_option(
        self,
    ):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": 0,
            "price_per_quarter": 0,
            "price_per_half": 0,
            "price_per_year": 0,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            subscription=subscription,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        price_per_month = model.plan.price_per_month
        price_per_quarter = model.plan.price_per_quarter
        price_per_half = model.plan.price_per_half
        price_per_year = model.plan.price_per_year
        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [model.cohort],
            [model.financing_option],
            model.currency,
            data={
                "amount_per_month": price_per_month,
                "amount_per_quarter": price_per_quarter,
                "amount_per_half": price_per_half,
                "amount_per_year": price_per_year,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": price_per_month,
                    "amount_per_quarter": price_per_quarter,
                    "amount_per_half": price_per_half,
                    "amount_per_year": price_per_year,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price, Plan with trial_duration and price et 0 and PlanFinancing
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__plan_already_financed(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": 0,
            "price_per_quarter": 0,
            "price_per_half": 0,
            "price_per_year": 0,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        plan_financing = {
            "valid_until": UTC_NOW - timedelta(seconds=1),
            "plan_expires_at": UTC_NOW - timedelta(seconds=1),
            "monthly_price": random.randint(1, 100),
        }
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            plan_financing=plan_financing,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = {"detail": "plan-already-financed", "status_code": 400}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price, Plan with trial_duration and price et 0 and Subscription that end in
    future
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__plan_already_bought__cancelled(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": random.random() * 100,
            "price_per_quarter": random.random() * 100,
            "price_per_half": random.random() * 100,
            "price_per_year": random.random() * 100,
            "is_renewable": True,
            "time_of_life": 0,
            "time_of_life_unit": None,
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {
            "valid_until": None,
            "next_payment_at": UTC_NOW + timedelta(seconds=1, days=2),
            "status": random.choice(["FREE_TRIAL", "ACTIVE", "PAYMENT_ISSUE", "ERROR", "EXPIRED"]),
        }

        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            subscription=subscription,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = {"detail": "plan-already-bought", "status_code": 400}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    """
    🔽🔽🔽 Get with one Bag, type is PREVIEW, passing type preview and many ServiceItem and Plan found,
    with the correct Currency and Price, Plan with trial_duration and price et 0 and Subscription that end in
    future
    """

    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__with_bag__type_bag__passing_type_preview__items_found__plan_already_bought__no_cancelled(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": random.random() * 100,
            "price_per_quarter": random.random() * 100,
            "price_per_half": random.random() * 100,
            "price_per_year": random.random() * 100,
            "is_renewable": True,
            "time_of_life": 0,
            "time_of_life_unit": None,
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {
            "valid_until": UTC_NOW + timedelta(seconds=1),
            "status": random.choice(["ACTIVE", "PAYMENT_ISSUE", "ERROR"]),
        }
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            subscription=subscription,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "academy": 1,
            "type": "PREVIEW",
            "plans": [1],
            "cohort_set": 1,
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        expected = {"detail": "plan-already-bought", "status_code": 400}

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    # When: Passing just the plan in the body without academy
    #    -> and the academy have a currency
    # Then: It should infer the academy from the plan to fill the bag
    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__inferring_academy_from_plan__no_linked(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": 0,
            "price_per_quarter": 0,
            "price_per_half": 0,
            "price_per_year": 0,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=1,
            subscription=subscription,
            skip_cohort=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "type": "PREVIEW",
            "plans": random.choices([model.plan.id, model.plan.slug], k=1),
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        price_per_month = model.plan.price_per_month
        price_per_quarter = model.plan.price_per_quarter
        price_per_half = model.plan.price_per_half
        price_per_year = model.plan.price_per_year
        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [],
            [model.financing_option],
            model.currency,
            data={
                "amount_per_month": price_per_month,
                "amount_per_quarter": price_per_quarter,
                "amount_per_half": price_per_half,
                "amount_per_year": price_per_year,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": price_per_month,
                    "amount_per_quarter": price_per_quarter,
                    "amount_per_half": price_per_half,
                    "amount_per_year": price_per_year,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    # When: Passing just the plan in the body without academy
    #    -> and the academy have a currency
    #    -> this plan have a EventTypeSet
    # Then: It should infer the academy from the plan to fill the bag
    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__inferring_academy_from_plan__linked_to_event_type_set(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": 0,
            "price_per_quarter": 0,
            "price_per_half": 0,
            "price_per_year": 0,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=1,
            event_type_set=1,
            subscription=subscription,
            skip_cohort=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "type": "PREVIEW",
            "plans": random.choices([model.plan.id, model.plan.slug], k=1),
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        price_per_month = model.plan.price_per_month
        price_per_quarter = model.plan.price_per_quarter
        price_per_half = model.plan.price_per_half
        price_per_year = model.plan.price_per_year
        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [],
            [model.financing_option],
            model.currency,
            data={
                "amount_per_month": price_per_month,
                "amount_per_quarter": price_per_quarter,
                "amount_per_half": price_per_half,
                "amount_per_year": price_per_year,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": price_per_month,
                    "amount_per_quarter": price_per_quarter,
                    "amount_per_half": price_per_half,
                    "amount_per_year": price_per_year,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    # When: Passing just the plan in the body without academy
    #    -> and the academy have a currency
    # Then: It should infer the academy from the plan to fill the bag,
    #    -> but the plan have a cohort linked, take it as selected cohort
    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__inferring_academy_from_plan__linked_to_1_cohort(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": 0,
            "price_per_quarter": 0,
            "price_per_half": 0,
            "price_per_year": 0,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=1,
            subscription=subscription,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "type": "PREVIEW",
            "plans": random.choices([model.plan.id, model.plan.slug], k=1),
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        price_per_month = model.plan.price_per_month
        price_per_quarter = model.plan.price_per_quarter
        price_per_half = model.plan.price_per_half
        price_per_year = model.plan.price_per_year
        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [],
            [model.financing_option],
            model.currency,
            data={
                "amount_per_month": price_per_month,
                "amount_per_quarter": price_per_quarter,
                "amount_per_half": price_per_half,
                "amount_per_year": price_per_year,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": price_per_month,
                    "amount_per_quarter": price_per_quarter,
                    "amount_per_half": price_per_half,
                    "amount_per_year": price_per_year,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )

    # When: Passing just the cohort in the body without academy
    #    -> and the academy have a currency
    # Then: It should infer the academy from the cohort to fill the bag
    @patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
    def test__inferring_academy_from_cohort(self):
        bag = {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
        }

        currency = {"code": "USD", "name": "United States dollar"}

        plan = {
            "price_per_month": 0,
            "price_per_quarter": 0,
            "price_per_half": 0,
            "price_per_year": 0,
            "is_renewable": False,
            "time_of_life": random.randint(1, 100),
            "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
            "trial_duration": random.randint(1, 10),
        }

        service = {
            "price_per_unit": random.random() * 100,
        }

        how_many1 = random.randint(1, 5)
        possible_choices = [x for x in range(1, 6) if x != how_many1]
        how_many2 = random.choice(possible_choices)
        service_item = {"how_many": how_many1}
        subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}
        academy = {"available_as_saas": True}

        model = self.bc.database.create(
            user=1,
            bag=bag,
            academy=academy,
            subscription=subscription,
            cohort=1,
            cohort_set=1,
            service_item=service_item,
            service=service,
            plan=plan,
            plan_service_item=1,
            financing_option=1,
            currency=currency,
        )
        self.client.force_authenticate(model.user)

        service_item = self.bc.database.get("payments.ServiceItem", 1, dict=False)
        service_item.how_many = how_many2

        url = reverse_lazy("payments:checking")
        data = {
            "type": "PREVIEW",
            "plans": random.choices([model.plan.id, model.plan.slug], k=1),
            "cohort_set": random.choice([model.cohort_set.id, model.cohort_set.slug]),
        }

        token = self.bc.random.string(lower=True, upper=True, number=True, size=40)
        with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
            response = self.client.put(url, data, format="json")

        json = response.json()

        price_per_month = model.plan.price_per_month
        price_per_quarter = model.plan.price_per_quarter
        price_per_half = model.plan.price_per_half
        price_per_year = model.plan.price_per_year
        expected = get_serializer(
            model.bag,
            [model.plan],
            [model.service_item],
            [],
            model.service,
            [],
            [model.financing_option],
            model.currency,
            data={
                "amount_per_month": price_per_month,
                "amount_per_quarter": price_per_quarter,
                "amount_per_half": price_per_half,
                "amount_per_year": price_per_year,
                "expires_at": self.bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
                "token": token,
                "is_recurrent": True,
            },
        )

        self.assertEqual(json, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            self.bc.database.list_of("payments.Bag"),
            [
                {
                    **self.bc.format.to_dict(model.bag),
                    "amount_per_month": price_per_month,
                    "amount_per_quarter": price_per_quarter,
                    "amount_per_half": price_per_half,
                    "amount_per_year": price_per_year,
                    "expires_at": UTC_NOW + timedelta(minutes=60),
                    "token": token,
                    "is_recurrent": True,
                },
            ],
        )
        self.assertEqual(
            self.bc.database.list_of("authenticate.UserSetting"),
            [
                format_user_setting(
                    {
                        "lang": "en",
                        "id": model.user.id,
                        "user_id": model.user.id,
                    }
                ),
            ],
        )
        self.bc.check.queryset_with_pks(model.bag.service_items.all(), [])
        self.bc.check.queryset_with_pks(model.bag.plans.all(), [1])
        self.bc.check.calls(
            activity_tasks.add_activity.delay.call_args_list,
            [
                call(1, "bag_created", related_type="payments.Bag", related_id=1),
            ],
        )


def test_exceding_coupon_limit(bc: Breathecode, client: APIClient):
    bag = {
        "status": "CHECKING",
        "type": "PREVIEW",
        "plans": [],
        "service_items": [],
        "coupons": [],
    }

    currency = {"code": "USD", "name": "United States dollar"}

    plan = {
        "price_per_month": 0,
        "price_per_quarter": 0,
        "price_per_half": 0,
        "price_per_year": 0,
        "is_renewable": False,
        "time_of_life": random.randint(1, 100),
        "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
        "trial_duration": random.randint(1, 10),
    }

    service = {
        "price_per_unit": random.random() * 100,
    }

    how_many1 = random.randint(1, 5)
    possible_choices = [x for x in range(1, 6) if x != how_many1]
    how_many2 = random.choice(possible_choices)
    service_item = {"how_many": how_many1}
    subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}
    academy = {"available_as_saas": True}
    coupon = {
        "discount_value": random.random() * 100,
        "offered_at": None,
        "expires_at": None,
        "auto": False,
        "how_many_offers": random.randint(1, 5),
    }

    model = bc.database.create(
        user=1,
        bag=bag,
        coupon=(2, coupon),
        academy=academy,
        subscription=subscription,
        cohort=1,
        cohort_set=1,
        service_item=service_item,
        service=service,
        plan=plan,
        plan_service_item=1,
        financing_option=1,
        currency=currency,
    )
    client.force_authenticate(model.user)

    service_item = bc.database.get("payments.ServiceItem", 1, dict=False)
    service_item.how_many = how_many2

    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "cohort_set": 1,
        "coupons": [x.slug for x in model.coupon],
    }

    token = bc.random.string(lower=True, upper=True, number=True, size=40)
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    json = response.json()

    price_per_month = model.plan.price_per_month
    price_per_quarter = model.plan.price_per_quarter
    price_per_half = model.plan.price_per_half
    price_per_year = model.plan.price_per_year
    expected = {
        "detail": "too-many-coupons",
        "status_code": 400,
    }

    assert json == expected
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert bc.database.list_of("payments.Bag") == [
        {
            **bc.format.to_dict(model.bag),
            "amount_per_month": price_per_month,
            "amount_per_quarter": price_per_quarter,
            "amount_per_half": price_per_half,
            "amount_per_year": price_per_year,
            "expires_at": None,
            "token": None,
        },
    ]
    assert bc.database.list_of("authenticate.UserSetting") == [
        format_user_setting(
            {
                "lang": "en",
                "id": model.user.id,
                "user_id": model.user.id,
            }
        ),
    ]
    queryset_with_pks(model.bag.service_items.all(), [])
    queryset_with_pks(model.bag.plans.all(), [])
    queryset_with_pks(model.bag.coupons.all(), [])
    bc.check.calls(
        activity_tasks.add_activity.delay.call_args_list,
        [
            call(1, "bag_created", related_type="payments.Bag", related_id=1),
        ],
    )


@pytest.mark.parametrize("how_many_offers", [-1, 10])
@pytest.mark.parametrize(
    "offered_at, expires_at",
    [
        (None, None),
        (UTC_NOW - timedelta(days=10), None),
        (UTC_NOW - timedelta(days=10), UTC_NOW + timedelta(days=10)),
    ],
)
def test_providing_coupons(bc: Breathecode, client: APIClient, how_many_offers, offered_at, expires_at):
    bag = {
        "status": "CHECKING",
        "type": "PREVIEW",
        "plans": [],
        "service_items": [],
        "coupons": [],
    }

    currency = {"code": "USD", "name": "United States dollar"}

    plan = {
        "price_per_month": 0,
        "price_per_quarter": 0,
        "price_per_half": 0,
        "price_per_year": 0,
        "is_renewable": False,
        "time_of_life": random.randint(1, 100),
        "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
        "trial_duration": random.randint(1, 10),
    }

    service = {
        "price_per_unit": random.random() * 100,
    }

    how_many1 = random.randint(1, 5)
    possible_choices = [x for x in range(1, 6) if x != how_many1]
    how_many2 = random.choice(possible_choices)
    service_item = {"how_many": how_many1}
    subscription = {"valid_until": UTC_NOW - timedelta(seconds=1)}
    academy = {"available_as_saas": True}
    coupons = [
        {
            "discount_value": random.random() * 100,
            "offered_at": offered_at,
            "expires_at": expires_at,
            "auto": auto,
            "how_many_offers": how_many_offers,
        }
        for auto in [True, True, False]
    ]

    model = bc.database.create(
        user=1,
        bag=bag,
        coupon=coupons,
        academy=academy,
        subscription=subscription,
        cohort=1,
        cohort_set=1,
        service_item=service_item,
        service=service,
        plan=plan,
        plan_service_item=1,
        financing_option=1,
        currency=currency,
    )
    client.force_authenticate(model.user)

    service_item = bc.database.get("payments.ServiceItem", 1, dict=False)
    service_item.how_many = how_many2

    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "cohort_set": 1,
        "coupons": [model.coupon[2].slug],
    }

    token = bc.random.string(lower=True, upper=True, number=True, size=40)
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    json = response.json()

    price_per_month = model.plan.price_per_month
    price_per_quarter = model.plan.price_per_quarter
    price_per_half = model.plan.price_per_half
    price_per_year = model.plan.price_per_year
    expected = get_serializer(
        model.bag,
        [model.plan],
        [model.service_item],
        [],
        model.service,
        [model.cohort],
        [model.financing_option],
        model.currency,
        coupons=model.coupon,
        data={
            "amount_per_month": price_per_month,
            "amount_per_quarter": price_per_quarter,
            "amount_per_half": price_per_half,
            "amount_per_year": price_per_year,
            "expires_at": bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
            "token": token,
            "is_recurrent": True,
        },
    )

    assert json == expected
    assert response.status_code == status.HTTP_200_OK

    assert bc.database.list_of("payments.Bag") == [
        {
            **bc.format.to_dict(model.bag),
            "amount_per_month": price_per_month,
            "amount_per_quarter": price_per_quarter,
            "amount_per_half": price_per_half,
            "amount_per_year": price_per_year,
            "expires_at": UTC_NOW + timedelta(minutes=60),
            "token": token,
            "is_recurrent": True,
        },
    ]
    assert bc.database.list_of("authenticate.UserSetting") == [
        format_user_setting(
            {
                "lang": "en",
                "id": model.user.id,
                "user_id": model.user.id,
            }
        ),
    ]
    queryset_with_pks(model.bag.service_items.all(), [])
    queryset_with_pks(model.bag.plans.all(), [1])
    queryset_with_pks(model.bag.coupons.all(), [1, 2, 3])
    bc.check.calls(
        activity_tasks.add_activity.delay.call_args_list,
        [
            call(1, "bag_created", related_type="payments.Bag", related_id=1),
        ],
    )


@pytest.mark.parametrize(
    "how_many_offers, how_many_subscriptions, how_many_plan_financings",
    [
        (-1, 0, 0),
        (6, 0, 0),
        (6, 5, 0),
        (6, 0, 5),
        (6, 3, 3),
    ],
)
@pytest.mark.parametrize(
    "offered_at, expires_at",
    [
        (None, None),
        (UTC_NOW - timedelta(days=10), None),
        (UTC_NOW - timedelta(days=10), UTC_NOW + timedelta(days=10)),
    ],
)
def test_getting_coupons(
    bc: Breathecode,
    client: APIClient,
    how_many_offers,
    offered_at,
    expires_at,
    how_many_subscriptions,
    how_many_plan_financings,
):
    auto = True
    bags = [
        {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
            "coupons": [],
            "user_id": 1,
        },
        {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
            "user_id": 2,
            "coupons": [1, 2, 3],
        },
    ]
    invoice = {"user_id": 2, "bag_id": 2}

    currency = {"code": "USD", "name": "United States dollar"}

    plan = {
        "price_per_month": 0,
        "price_per_quarter": 0,
        "price_per_half": 0,
        "price_per_year": 0,
        "is_renewable": False,
        "time_of_life": random.randint(1, 100),
        "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
        "trial_duration": random.randint(1, 10),
    }

    service = {
        "price_per_unit": random.random() * 100,
    }

    how_many1 = random.randint(1, 5)
    possible_choices = [x for x in range(1, 6) if x != how_many1]
    how_many2 = random.choice(possible_choices)
    service_item = {"how_many": how_many1}
    subscription = {
        "user_id": 2,
        "valid_until": UTC_NOW - timedelta(seconds=1),
    }
    plan_financing = {
        "user_id": 2,
        "plan_expires_at": UTC_NOW - timedelta(seconds=1),
        "monthly_price": random.random() * 100,
    }
    academy = {"available_as_saas": True}
    coupon = {
        "discount_value": random.random() * 100,
        "offered_at": offered_at,
        "expires_at": expires_at,
        "auto": auto,
        "how_many_offers": how_many_offers,
    }

    model = bc.database.create(
        user=2,
        subscription=(how_many_subscriptions, subscription),
        plan_financing=(how_many_plan_financings, plan_financing),
        bag=bags,
        invoice=invoice,
        coupon=(3, coupon),
        academy=academy,
        cohort=1,
        cohort_set=1,
        service_item=service_item,
        service=service,
        plan=plan,
        plan_service_item=1,
        financing_option=1,
        currency=currency,
    )
    client.force_authenticate(model.user[0])
    activity_tasks.add_activity.delay.call_args_list = []

    service_item = bc.database.get("payments.ServiceItem", 1, dict=False)
    service_item.how_many = how_many2

    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "cohort_set": 1,
    }

    token = bc.random.string(lower=True, upper=True, number=True, size=40)
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    json = response.json()

    price_per_month = model.plan.price_per_month
    price_per_quarter = model.plan.price_per_quarter
    price_per_half = model.plan.price_per_half
    price_per_year = model.plan.price_per_year
    expected = get_serializer(
        model.bag[0],
        [model.plan],
        [model.service_item],
        [],
        model.service,
        [model.cohort],
        [model.financing_option],
        model.currency,
        coupons=model.coupon,
        data={
            "amount_per_month": price_per_month,
            "amount_per_quarter": price_per_quarter,
            "amount_per_half": price_per_half,
            "amount_per_year": price_per_year,
            "expires_at": bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
            "token": token,
            "is_recurrent": False,
        },
    )

    assert json == expected
    assert response.status_code == status.HTTP_200_OK

    assert bc.database.list_of("payments.Bag") == [
        {
            **bc.format.to_dict(model.bag[0]),
            "amount_per_month": price_per_month,
            "amount_per_quarter": price_per_quarter,
            "amount_per_half": price_per_half,
            "amount_per_year": price_per_year,
            "expires_at": UTC_NOW + timedelta(minutes=60),
            "token": token,
            "is_recurrent": False,
        },
        bc.format.to_dict(model.bag[1]),
    ]
    assert bc.database.list_of("authenticate.UserSetting") == [
        format_user_setting(
            {
                "lang": "en",
                "id": 1,
                "user_id": model.user[1].id,
            }
        ),
        format_user_setting(
            {
                "lang": "en",
                "id": 2,
                "user_id": model.user[0].id,
            }
        ),
    ]

    queryset_with_pks(model.bag[0].service_items.all(), [])
    queryset_with_pks(model.bag[0].plans.all(), [1])
    queryset_with_pks(model.bag[0].coupons.all(), [1, 2, 3])
    queryset_with_pks(model.bag[1].service_items.all(), [])
    queryset_with_pks(model.bag[1].plans.all(), [])
    queryset_with_pks(model.bag[1].coupons.all(), [1, 2, 3])
    bc.check.calls(activity_tasks.add_activity.delay.call_args_list, [])


@pytest.mark.parametrize(
    "how_many_offers, offered_at, expires_at, how_many_subscriptions, how_many_plan_financings",
    [
        (0, None, None, 0, 0),
        (5, None, None, 6, 0),
        (5, None, None, 0, 6),
        (5, None, None, 3, 3),
        (6, UTC_NOW - timedelta(days=20), UTC_NOW - timedelta(days=10), 0, 0),
        (5, UTC_NOW - timedelta(days=10), UTC_NOW + timedelta(days=10), 6, 0),
        (5, UTC_NOW - timedelta(days=10), UTC_NOW + timedelta(days=10), 0, 6),
        (5, UTC_NOW - timedelta(days=10), UTC_NOW + timedelta(days=10), 3, 3),
    ],
)
def test_exausted_coupons(
    bc: Breathecode,
    client: APIClient,
    how_many_offers,
    offered_at,
    expires_at,
    how_many_subscriptions,
    how_many_plan_financings,
):
    bags = [
        {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
            "coupons": [],
            "user_id": 1,
        },
        {
            "status": "CHECKING",
            "type": "PREVIEW",
            "plans": [],
            "service_items": [],
            "user_id": 2,
            "coupons": [1, 2, 3],
        },
    ]
    invoice = {"user_id": 2, "bag_id": 2}

    currency = {"code": "USD", "name": "United States dollar"}

    plan = {
        "price_per_month": 0,
        "price_per_quarter": 0,
        "price_per_half": 0,
        "price_per_year": 0,
        "is_renewable": False,
        "time_of_life": random.randint(1, 100),
        "time_of_life_unit": random.choice(["DAY", "WEEK", "MONTH", "YEAR"]),
        "trial_duration": random.randint(1, 10),
    }

    service = {
        "price_per_unit": random.random() * 100,
    }

    how_many1 = random.randint(1, 5)
    possible_choices = [x for x in range(1, 6) if x != how_many1]
    how_many2 = random.choice(possible_choices)
    service_item = {"how_many": how_many1}
    subscription = {
        "user_id": 2,
        "valid_until": UTC_NOW - timedelta(seconds=1),
    }
    plan_financing = {
        "user_id": 2,
        "plan_expires_at": UTC_NOW - timedelta(seconds=1),
        "monthly_price": random.random() * 100,
    }
    academy = {"available_as_saas": True}
    coupons = [
        {
            "discount_value": random.random() * 100,
            "offered_at": offered_at,
            "expires_at": expires_at,
            "auto": auto,
            "how_many_offers": how_many_offers,
        }
        for auto in [True, True, False]
    ]

    model = bc.database.create(
        user=2,
        bag=bags,
        invoice=invoice,
        coupon=coupons,
        academy=academy,
        subscription=(how_many_subscriptions, subscription),
        plan_financing=(how_many_plan_financings, plan_financing),
        cohort=1,
        cohort_set=1,
        service_item=service_item,
        service=service,
        plan=plan,
        plan_service_item=1,
        financing_option=1,
        currency=currency,
    )
    client.force_authenticate(model.user[0])
    activity_tasks.add_activity.delay.call_args_list = []

    service_item = bc.database.get("payments.ServiceItem", 1, dict=False)
    service_item.how_many = how_many2

    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "cohort_set": 1,
        "coupons": [model.coupon[2].slug],
    }

    token = bc.random.string(lower=True, upper=True, number=True, size=40)
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    json = response.json()

    price_per_month = model.plan.price_per_month
    price_per_quarter = model.plan.price_per_quarter
    price_per_half = model.plan.price_per_half
    price_per_year = model.plan.price_per_year
    expected = get_serializer(
        model.bag[0],
        [model.plan],
        [model.service_item],
        [],
        model.service,
        [model.cohort],
        [model.financing_option],
        model.currency,
        data={
            "amount_per_month": price_per_month,
            "amount_per_quarter": price_per_quarter,
            "amount_per_half": price_per_half,
            "amount_per_year": price_per_year,
            "expires_at": bc.datetime.to_iso_string(UTC_NOW + timedelta(minutes=60)),
            "token": token,
            "is_recurrent": False,
        },
    )

    assert json == expected
    assert response.status_code == status.HTTP_200_OK

    assert bc.database.list_of("payments.Bag") == [
        {
            **bc.format.to_dict(model.bag[0]),
            "amount_per_month": price_per_month,
            "amount_per_quarter": price_per_quarter,
            "amount_per_half": price_per_half,
            "amount_per_year": price_per_year,
            "expires_at": UTC_NOW + timedelta(minutes=60),
            "token": token,
            "is_recurrent": False,
        },
        bc.format.to_dict(model.bag[1]),
    ]
    assert bc.database.list_of("authenticate.UserSetting") == [
        format_user_setting(
            {
                "lang": "en",
                "id": 1,
                "user_id": model.user[1].id,
            }
        ),
        format_user_setting(
            {
                "lang": "en",
                "id": 2,
                "user_id": model.user[0].id,
            }
        ),
    ]
    queryset_with_pks(model.bag[0].service_items.all(), [])
    queryset_with_pks(model.bag[0].plans.all(), [1])
    queryset_with_pks(model.bag[0].coupons.all(), [])
    queryset_with_pks(model.bag[1].service_items.all(), [])
    queryset_with_pks(model.bag[1].plans.all(), [])
    queryset_with_pks(model.bag[1].coupons.all(), [1, 2, 3])
    bc.check.calls(activity_tasks.add_activity.delay.call_args_list, [])


@patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
def test_so_much_service_items(
    database: capy.Database,
    client: capy.Client,
    fake: capy.Fake,
    format: capy.Format,
):
    bag = {
        "status": "CHECKING",
        "type": "PREVIEW",
        "plans": [],
        "service_items": [],
    }

    currency = {"code": "USD", "name": "United States dollar"}

    plan = {
        "price_per_month": random.random() * 100,
        "price_per_quarter": random.random() * 100,
        "price_per_half": random.random() * 100,
        "price_per_year": random.random() * 100,
        "is_renewable": True,
        "time_of_life": 0,
        "time_of_life_unit": None,
    }

    how_many1 = random.randint(1, 5)
    possible_choices = [x for x in range(5, 7) if x != how_many1]
    how_many2 = random.choice(possible_choices)
    service_item = {"how_many": how_many1}
    academy = {"available_as_saas": True}

    model = database.create(
        user=1,
        bag=bag,
        academy=academy,
        cohort=1,
        cohort_set=1,
        service_item=service_item,
        service=1,
        academy_service={"bundle_size": 2, "max_items": 4, "max_amount": 4},
        plan=plan,
        plan_service_item=1,
        currency=currency,
        city=1,
        country=1,
    )

    # issue with capy database
    model.bag.service_items.set([])
    model.bag.plans.set([])

    client.force_authenticate(model.user)

    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "cohort_set": 1,
        "service_items": [{"how_many": how_many2, "service": 1}],
    }

    token = fake.slug()
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    json = response.json()
    expected = {"detail": "the-amount-of-items-is-too-high", "status_code": 400}

    assert json == expected
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert database.list_of("payments.Bag") == [
        {
            **format.to_obj_repr(model.bag),
        },
    ]
    assert database.list_of("authenticate.UserSetting") == [
        format_user_setting(
            {
                "lang": "en",
                "id": model.user.id,
                "user_id": model.user.id,
            }
        ),
    ]

    queryset_with_pks(model.bag.service_items.all(), [])
    queryset_with_pks(model.bag.plans.all(), [])
    assert activity_tasks.add_activity.delay.call_args_list == [
        call(1, "bag_created", related_type="payments.Bag", related_id=1),
    ]


@patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
def test_so_low_service_items(
    database: capy.Database,
    client: capy.Client,
    fake: capy.Fake,
    format: capy.Format,
):
    bag = {
        "status": "CHECKING",
        "type": "PREVIEW",
        "plans": [],
        "service_items": [],
    }

    currency = {"code": "USD", "name": "United States dollar"}

    plan = {
        "price_per_month": random.random() * 100,
        "price_per_quarter": random.random() * 100,
        "price_per_half": random.random() * 100,
        "price_per_year": random.random() * 100,
        "is_renewable": True,
        "time_of_life": 0,
        "time_of_life_unit": None,
    }

    how_many1 = random.randint(1, 5)
    possible_choices = [x for x in range(1, 3) if x != how_many1]
    how_many2 = random.choice(possible_choices)
    service_item = {"how_many": how_many1}
    academy = {"available_as_saas": True}

    model = database.create(
        user=1,
        bag=bag,
        academy=academy,
        cohort=1,
        cohort_set=1,
        service_item=service_item,
        service=1,
        academy_service={"bundle_size": 4, "max_items": 7, "max_amount": 7},
        plan=plan,
        plan_service_item=1,
        currency=currency,
        city=1,
        country=1,
    )

    # issue with capy database
    model.bag.service_items.set([])
    model.bag.plans.set([])

    client.force_authenticate(model.user)

    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "cohort_set": 1,
        "service_items": [{"how_many": how_many2, "service": 1}],
    }

    token = fake.slug()
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    json = response.json()
    expected = {"detail": "the-amount-of-items-is-too-low", "status_code": 400}

    assert json == expected
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert database.list_of("payments.Bag") == [
        {
            **format.to_obj_repr(model.bag),
        },
    ]
    assert database.list_of("authenticate.UserSetting") == [
        format_user_setting(
            {
                "lang": "en",
                "id": model.user.id,
                "user_id": model.user.id,
            }
        ),
    ]

    queryset_with_pks(model.bag.service_items.all(), [])
    queryset_with_pks(model.bag.plans.all(), [])
    assert activity_tasks.add_activity.delay.call_args_list == [
        call(1, "bag_created", related_type="payments.Bag", related_id=1),
    ]


@patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
def test_price_is_very_high(
    database: capy.Database,
    client: capy.Client,
    fake: capy.Fake,
    format: capy.Format,
):
    bag = {
        "status": "CHECKING",
        "type": "PREVIEW",
        "plans": [],
        "service_items": [],
    }

    currency = {"code": "USD", "name": "United States dollar"}

    plan = {
        "price_per_month": random.random() * 100,
        "price_per_quarter": random.random() * 100,
        "price_per_half": random.random() * 100,
        "price_per_year": random.random() * 100,
        "is_renewable": True,
        "time_of_life": 0,
        "time_of_life_unit": None,
    }

    how_many1 = random.randint(1, 5)
    possible_choices = [x for x in range(4, 7) if x != how_many1]
    how_many2 = random.choice(possible_choices)
    service_item = {"how_many": how_many1}
    academy = {"available_as_saas": True}

    model = database.create(
        user=1,
        bag=bag,
        academy=academy,
        cohort=1,
        cohort_set=1,
        service_item=service_item,
        service=1,
        academy_service={"bundle_size": 4, "max_items": 7, "price_per_unit": 1, "max_amount": 3},
        plan=plan,
        plan_service_item=1,
        currency=currency,
        city=1,
        country=1,
    )

    # issue with capy database
    model.bag.service_items.set([])
    model.bag.plans.set([])

    client.force_authenticate(model.user)

    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "cohort_set": 1,
        "service_items": [{"how_many": how_many2, "service": 1}],
    }

    token = fake.slug()
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    json = response.json()
    expected = {"detail": "the-amount-is-too-high", "status_code": 400}

    assert json == expected
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert database.list_of("payments.Bag") == [
        {
            **format.to_obj_repr(model.bag),
        },
    ]
    assert database.list_of("authenticate.UserSetting") == [
        format_user_setting(
            {
                "lang": "en",
                "id": model.user.id,
                "user_id": model.user.id,
            }
        ),
    ]

    queryset_with_pks(model.bag.service_items.all(), [])
    queryset_with_pks(model.bag.plans.all(), [])
    assert activity_tasks.add_activity.delay.call_args_list == [
        call(1, "bag_created", related_type="payments.Bag", related_id=1),
    ]


@patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
def test_get_a_plan_with_add_ons(
    database: capy.Database,
    client: capy.Client,
    fake: capy.Fake,
    format: capy.Format,
):
    bag = {
        "status": "CHECKING",
        "type": "PREVIEW",
        "plans": [],
        "service_items": [],
    }

    currency = {"code": "USD", "name": "United States dollar"}

    plan = {
        "price_per_month": random.random() * 100,
        "price_per_quarter": random.random() * 100,
        "price_per_half": random.random() * 100,
        "price_per_year": random.random() * 100,
        "is_renewable": True,
        "time_of_life": 0,
        "time_of_life_unit": None,
        "trial_duration": 0,
        "trial_duration_unit": "MONTH",
    }

    how_many2 = random.choice([x for x in range(5, 6)])

    service_item = {"how_many": how_many2}
    academy = {"available_as_saas": True}

    model = database.create(
        user=1,
        bag=bag,
        academy=academy,
        cohort=1,
        cohort_set=1,
        service_item=service_item,
        service=1,
        academy_service={"bundle_size": 4, "max_items": 7, "price_per_unit": 1, "max_amount": 7},
        plan=plan,
        currency=currency,
        city=1,
        country=1,
    )

    # issue with capy database
    model.bag.service_items.set([])
    model.bag.plans.set([])

    client.force_authenticate(model.user)

    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "cohort_set": 1,
        "service_items": [{"how_many": how_many2, "service": 1}],
    }

    token = fake.slug()
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    price, _, _ = model.academy_service.get_discounted_price(how_many2)
    pricing = {
        "amount_per_month": model.plan.price_per_month + price,
        "amount_per_quarter": model.plan.price_per_quarter + price,
        "amount_per_half": model.plan.price_per_half + price,
        "amount_per_year": model.plan.price_per_year + price,
    }

    json = response.json()
    expected = get_serializer(
        model.bag,
        data={
            "expires_at": (UTC_NOW + timedelta(minutes=60)).isoformat().replace("+00:00", "Z"),
            "token": token,
            "is_recurrent": True,
            **pricing,
        },
        plans=[model.plan],
        service_items=[model.service_item],
        plan_service_items=[model.service_item],
        service=model.service,
    )

    assert json == expected
    assert response.status_code == status.HTTP_200_OK

    assert database.list_of("payments.Bag") == [
        {
            **format.to_obj_repr(model.bag),
            **pricing,
            "token": token,
            "expires_at": UTC_NOW + timedelta(minutes=60),
            "is_recurrent": True,
        },
    ]
    assert database.list_of("authenticate.UserSetting") == [
        format_user_setting(
            {
                "lang": "en",
                "id": model.user.id,
                "user_id": model.user.id,
            }
        ),
    ]

    queryset_with_pks(model.bag.service_items.all(), [1])
    queryset_with_pks(model.bag.plans.all(), [1])
    assert activity_tasks.add_activity.delay.call_args_list == [
        call(1, "bag_created", related_type="payments.Bag", related_id=1),
    ]


@pytest.mark.parametrize(
    "country_code,ratio,price_per_month,price_per_quarter,price_per_half,price_per_year",
    [
        ("ve", 0.8, 80.0, 216.0, 384.0, 720.0),  # Venezuela with general ratio
        ("ar", 0.7, 70.0, 189.0, 336.0, 630.0),  # Argentina with general ratio
        ("us", 1.0, 100.0, 270.0, 480.0, 900.0),  # US with default ratio
        (None, 1.0, 100.0, 270.0, 480.0, 900.0),  # No country code
    ],
)
@patch("breathecode.payments.actions.apply_pricing_ratio")
def test_checking_with_country_pricing(
    mock_apply_pricing_ratio,
    database: capy.Database,
    client: capy.Client,
    fake: capy.Fake,
    format: capy.Format,
    country_code,
    ratio,
    price_per_month,
    price_per_quarter,
    price_per_half,
    price_per_year,
):
    """
    Test that the checking endpoint correctly calculates prices based on country code
    by mocking apply_pricing_ratio.
    """

    # Define the side effect for the mock
    def side_effect(price, country_code, obj, lang=None, price_attr="price", cache=None):
        # Simulate the logic based on the parameters passed to this test
        if country_code == "ve":
            return price * 0.8, 0.8, None
        if country_code == "ar":
            return price * 0.7, 0.7, None
        if country_code == "us":
            return price * 1.0, 1.0, None
        # Fallback for other or no country code
        return price, None, None

    mock_apply_pricing_ratio.side_effect = side_effect

    # Setup test data
    bag = {
        "id": 1,
        "academy": {
            "id": 1,
            "logo_url": "",
            "name": "test",
            "slug": "test",
        },
        "status": "CHECKING",
        "type": "PREVIEW",
        "plans": [],
        "amount_per_month": price_per_month,
        "amount_per_quarter": price_per_quarter,
        "amount_per_half": price_per_half,
        "amount_per_year": price_per_year,
        "token": "abc",
        "user": {"id": 1, "email": "john@example.com", "first_name": "John", "last_name": "Doe"},
        "was_delivered": False,
        "expires_at": UTC_NOW + timedelta(days=10),
        "created_at": UTC_NOW,
        "updated_at": UTC_NOW,
    }

    model = database.create(
        country=1,
        city=1,
        academy={"id": 1, "name": "test", "slug": "test", "available_as_saas": True},
        plan={
            "id": 1,
            "slug": "test",
            "price_per_month": 100.0,
            "price_per_quarter": 270.0,
            "price_per_half": 480.0,
            "price_per_year": 900.0,
            "time_of_life": 0,
            "time_of_life_unit": None,
            "trial_duration": 0,
            "trial_duration_unit": "MONTH",
            "is_renewable": True,
        },
        currency={"code": "USD", "name": "United States dollar"},
        user={"id": 1, "email": "john@example.com", "first_name": "John", "last_name": "Doe"},
        bag=bag,
    )

    payload = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
    }

    if country_code:
        payload["country_code"] = country_code

    client.force_authenticate(model.user)
    url = reverse_lazy("payments:checking")
    response = client.put(url, payload, format="json")

    # Assert the response is correct
    assert response.status_code == 200

    data = response.json()
    assert data["amount_per_month"] == price_per_month
    assert data["amount_per_quarter"] == price_per_quarter
    assert data["amount_per_half"] == price_per_half
    assert data["amount_per_year"] == price_per_year

    # Verify apply_pricing_ratio was called if country_code was provided
    if country_code:
        # Check that it was called at least once for any price
        assert mock_apply_pricing_ratio.call_count > 0


@patch("django.utils.timezone.now", MagicMock(return_value=UTC_NOW))
def test_checking_with_country_price_override(
    database: capy.Database,
    client: capy.Client,
    fake: capy.Fake,
    format: capy.Format,
    set_datetime,
):
    """
    Test that the checking endpoint correctly uses the price override from
    pricing_ratio_exceptions for a specific country.
    """
    set_datetime(UTC_NOW)
    country_code = "VE"
    override_price_per_month = 50.0
    override_price_per_quarter = 135.0
    override_price_per_half = 240.0
    override_price_per_year = 450.0

    plan_kwargs = {
        "price_per_month": 100.0,
        "price_per_quarter": 270.0,
        "price_per_half": 480.0,
        "price_per_year": 900.0,
        "is_renewable": True,
        "time_of_life": 0,
        "time_of_life_unit": None,
        "trial_duration": 0,
        "pricing_ratio_exceptions": {
            country_code.lower(): {
                "price_per_month": override_price_per_month,
                "price_per_quarter": override_price_per_quarter,
                "price_per_half": override_price_per_half,
                "price_per_year": override_price_per_year,
                "currency": "USD",  # Ensure currency is specified if overridden
            }
        },
    }
    model = database.create(
        country=1,
        city=1,
        user=1,
        academy=1,
        currency={"code": "USD"},
        plan=plan_kwargs,
    )

    client.force_authenticate(model.user)
    url = reverse_lazy("payments:checking")
    data = {
        "academy": 1,
        "type": "PREVIEW",
        "plans": [1],
        "country_code": country_code,
    }

    token = fake.slug()
    with patch("rest_framework.authtoken.models.Token.generate_key", MagicMock(return_value=token)):
        response = client.put(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    json_data = response.json()

    # Verify the amounts in the response match the override prices
    assert json_data["amount_per_month"] == override_price_per_month
    assert json_data["amount_per_quarter"] == override_price_per_quarter
    assert json_data["amount_per_half"] == override_price_per_half
    assert json_data["amount_per_year"] == override_price_per_year
    assert json_data["token"] == token
    assert json_data["expires_at"] == (UTC_NOW + timedelta(minutes=60)).isoformat().replace("+00:00", "Z")

    # Verify the bag in the database reflects the override
    db_bag = database.list_of("payments.Bag")[0]
    assert db_bag["amount_per_month"] == override_price_per_month
    assert db_bag["amount_per_quarter"] == override_price_per_quarter
    assert db_bag["amount_per_half"] == override_price_per_half
    assert db_bag["amount_per_year"] == override_price_per_year
    assert db_bag["country_code"] == country_code
    assert db_bag["currency_id"] == model.currency.id
    assert db_bag["token"] == token
    assert db_bag["expires_at"] == UTC_NOW + timedelta(minutes=60)
    # Since a direct price override was used, the explanation should be empty
    assert db_bag["pricing_ratio_explanation"] == {
        "plans": [
            {
                "plan": model.plan.slug,
                "ratio": None,
            },
        ],
        "service_items": [],
    }

    assert activity_tasks.add_activity.delay.call_args_list == [
        call(1, "bag_created", related_type="payments.Bag", related_id=1),
    ]
