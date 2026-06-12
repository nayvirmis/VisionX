from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
import requests
import responses

from app.errors import UpstreamError
from app.services.x_api import API_BASE, get_public_posts


def account():
    return SimpleNamespace(
        username="alice_x",
        display_name="Alice X",
        profile_image_url="https://example.com/avatar.png",
        verified=True,
    )


@responses.activate
def test_public_posts_use_the_app_bearer_and_normalize_media(app):
    responses.get(
        f"{API_BASE}/2/users/123/tweets",
        json={
            "data": [
                {
                    "id": "post-1",
                    "text": "Public post",
                    "created_at": "2026-06-12T10:00:00Z",
                    "attachments": {"media_keys": ["media-1"]},
                    "public_metrics": {
                        "reply_count": 1,
                        "retweet_count": 2,
                        "like_count": 3,
                        "quote_count": 4,
                        "impression_count": 5,
                    },
                }
            ],
            "includes": {
                "media": [
                    {
                        "media_key": "media-1",
                        "type": "photo",
                        "url": "https://example.com/photo.jpg",
                    }
                ]
            },
        },
    )

    with app.app_context():
        posts = get_public_posts("123", account())

    request = responses.calls[0].request
    query = parse_qs(urlparse(request.url).query)
    assert request.headers["Authorization"] == "Bearer test-bearer"
    assert query["exclude"] == ["replies,retweets"]
    assert posts[0]["author"]["username"] == "alice_x"
    assert posts[0]["media"][0]["url"] == "https://example.com/photo.jpg"
    assert posts[0]["metrics"]["views"] == 5


@responses.activate
def test_x_rate_limit_preserves_retry_after(app):
    responses.get(
        f"{API_BASE}/2/users/123/tweets",
        status=429,
        headers={"Retry-After": "120"},
    )

    with app.app_context(), pytest.raises(UpstreamError) as error:
        get_public_posts("123", account())

    assert error.value.code == "x_rate_limited"
    assert error.value.headers["Retry-After"] == "120"


@responses.activate
def test_x_network_failure_is_structured(app):
    responses.get(
        f"{API_BASE}/2/users/123/tweets",
        body=requests.ConnectionError("offline"),
    )

    with app.app_context(), pytest.raises(UpstreamError) as error:
        get_public_posts("123", account())

    assert error.value.code == "x_api_error"
