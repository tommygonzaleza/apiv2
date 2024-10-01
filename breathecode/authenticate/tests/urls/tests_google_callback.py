"""
Test /v1/auth/subscribe
"""

from datetime import datetime, timedelta
import random
from unittest.mock import call

import pytest
from django.urls.base import reverse_lazy
from rest_framework import status

import capyc.pytest as capy
import staging.pytest as staging
from urllib.parse import quote


@pytest.fixture(autouse=True)
def setup(monkeypatch: pytest.MonkeyPatch, db):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "123456.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_SECRET", "123456")
    monkeypatch.setenv("GOOGLE_REDIRECT_URL", "https://breathecode.herokuapp.com/v1/auth/google/callback")

    yield


@pytest.fixture
def validation_res(patch_request):
    validation_res = {
        "quality_score": (random.random() * 0.4) + 0.6,
        "email_quality": (random.random() * 0.4) + 0.6,
        "is_valid_format": {
            "value": True,
        },
        "is_mx_found": {
            "value": True,
        },
        "is_smtp_valid": {
            "value": True,
        },
        "is_catchall_email": {
            "value": True,
        },
        "is_role_email": {
            "value": True,
        },
        "is_disposable_email": {
            "value": False,
        },
        "is_free_email": {
            "value": True,
        },
    }
    patch_request(
        [
            (
                call(
                    "get",
                    "https://emailvalidation.abstractapi.com/v1/?api_key=None&email=pokemon@potato.io",
                    params=None,
                    timeout=10,
                ),
                validation_res,
            ),
        ]
    )
    return validation_res


def test_no_token(database: capy.Database, client: capy.Client):
    url = reverse_lazy("authenticate:google_callback")

    response = client.get(url, format="json")

    json = response.json()
    expected = {"detail": "no-callback-url", "status_code": 400}

    assert json == expected
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert database.list_of("authenticate.Token") == []
    assert database.list_of("authenticate.CredentialsGoogle") == []


def test_no_url(database: capy.Database, client: capy.Client):
    url = reverse_lazy("authenticate:google_callback") + "?state=url%3Dhttps://4geeks.com"

    response = client.get(url, format="json")

    json = response.json()
    expected = {"detail": "no-user-token", "status_code": 400}

    assert json == expected
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert database.list_of("authenticate.Token") == []
    assert database.list_of("authenticate.CredentialsGoogle") == []


def test_no_code(database: capy.Database, client: capy.Client):
    url = reverse_lazy("authenticate:google_callback") + "?state=token%3Dabc123%26url%3Dhttps://4geeks.com"

    response = client.get(url, format="json")

    json = response.json()
    expected = {"detail": "no-code", "status_code": 400}

    assert json == expected
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert database.list_of("authenticate.Token") == []
    assert database.list_of("authenticate.CredentialsGoogle") == []


def test_token_not_found(database: capy.Database, client: capy.Client):
    url = (
        reverse_lazy("authenticate:google_callback")
        + "?state=token%3Dabc123%26url%3Dhttps://4geeks.com&code=12345&scope=https://www.googleapis.com/auth/calendar.events"
    )

    response = client.get(url, format="json")

    json = response.json()
    expected = {"detail": "token-not-found", "status_code": 404}

    assert json == expected
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert database.list_of("authenticate.Token") == []
    assert database.list_of("authenticate.CredentialsGoogle") == []


def test_token(
    database: capy.Database, client: capy.Client, format: capy.Format, utc_now: datetime, http: staging.HTTP
):
    model = database.create(token={"token_type": "temporal"})
    url = (
        reverse_lazy("authenticate:google_callback")
        + f"?state=token%3D{model.token.key}%26url%3Dhttps://4geeks.com&code=12345&scope=https://www.googleapis.com/auth/calendar.events"
    )

    payload = {
        "client_id": "123456.apps.googleusercontent.com",
        "client_secret": "123456",
        "redirect_uri": "https://breathecode.herokuapp.com/v1/auth/google/callback",
        "grant_type": "authorization_code",
        "code": "12345",
    }

    http.post(
        "https://oauth2.googleapis.com/token",
        json=payload,
        headers={"Accept": "application/json"},
    ).response(
        {"access_token": "test_access_token", "expires_in": 3600, "refresh_token": "test_refresh_token"}, status=200
    )

    response = client.get(url, format="json")

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == f"https://4geeks.com?token={quote(model.token.key)}"

    http.call_count == 1

    assert database.list_of("authenticate.Token") == [format.to_obj_repr(model.token)]
    assert database.list_of("authenticate.CredentialsGoogle") == [
        {
            "expires_at": utc_now + timedelta(seconds=3600),
            "id": 1,
            "refresh_token": "test_refresh_token",
            "token": "test_access_token",
            "user_id": 1,
        },
    ]