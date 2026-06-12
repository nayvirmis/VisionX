from urllib.parse import urlencode

import requests
from flask import current_app

from ..errors import ApiError, UpstreamError

API_BASE = "https://api.x.com"
AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"


def request_x(method, url, **kwargs):
    try:
        return requests.request(method, url, **kwargs)
    except requests.RequestException as exc:
        raise UpstreamError("The X API is temporarily unavailable.") from exc


def response_json(response, message):
    try:
        return response.json()
    except requests.JSONDecodeError as exc:
        raise UpstreamError(message, details=response.text) from exc


def authorization_url(state, code_challenge):
    params = {
        "response_type": "code",
        "client_id": current_app.config["X_CLIENT_ID"],
        "redirect_uri": current_app.config["X_REDIRECT_URI"],
        "scope": "tweet.read users.read",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(code, code_verifier):
    response = request_x(
        "POST",
        f"{API_BASE}/2/oauth2/token",
        auth=(
            current_app.config["X_CLIENT_ID"],
            current_app.config["X_CLIENT_SECRET"],
        ),
        data={
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": current_app.config["X_REDIRECT_URI"],
            "code_verifier": code_verifier,
        },
        timeout=15,
    )
    if not response.ok:
        raise UpstreamError("X rejected the OAuth code.", details=response.text)
    payload = response_json(response, "X returned an invalid OAuth response.")
    access_token = payload.get("access_token")
    if not access_token:
        raise UpstreamError("X returned an invalid OAuth response.")
    return access_token


def get_authenticated_user(access_token):
    response = request_x(
        "GET",
        f"{API_BASE}/2/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"user.fields": "id,name,username,profile_image_url,protected,verified"},
        timeout=15,
    )
    if not response.ok:
        raise UpstreamError("Unable to verify the X account.", details=response.text)
    payload = response_json(response, "X returned an invalid account response.")
    if not payload.get("data"):
        raise UpstreamError("X returned an invalid account response.")
    return payload["data"]


def get_public_posts(x_user_id, fallback_user):
    bearer_token = current_app.config["X_BEARER_TOKEN"]
    if not bearer_token:
        raise ApiError("X feed retrieval is not configured.", 503, "x_not_configured")
    response = request_x(
        "GET",
        f"{API_BASE}/2/users/{x_user_id}/tweets",
        headers={"Authorization": f"Bearer {bearer_token}"},
        params={
            "max_results": 25,
            "exclude": "replies,retweets",
            "tweet.fields": "id,text,created_at,public_metrics,attachments,entities",
            "expansions": "attachments.media_keys",
            "media.fields": "media_key,type,url,preview_image_url,variants",
        },
        timeout=20,
    )
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "60")
        raise UpstreamError(
            "X API rate limit reached. Try again later.",
            503,
            "x_rate_limited",
            headers={"Retry-After": retry_after},
        )
    if not response.ok:
        raise UpstreamError("Unable to load public posts from X.", details=response.text)

    payload = response_json(response, "X returned an invalid feed response.")
    media_by_key = {
        media["media_key"]: media for media in payload.get("includes", {}).get("media", [])
    }
    return [normalize_post(post, media_by_key, fallback_user) for post in payload.get("data", [])]


def normalize_post(post, media_by_key, user):
    media_items = []
    for key in post.get("attachments", {}).get("media_keys", []):
        media = media_by_key.get(key, {})
        item = {
            "type": media.get("type"),
            "url": media.get("url") or media.get("preview_image_url"),
        }
        variants = media.get("variants", [])
        video_variants = [
            variant
            for variant in variants
            if variant.get("content_type") == "video/mp4" and variant.get("url")
        ]
        if video_variants:
            item["url"] = max(video_variants, key=lambda value: value.get("bit_rate", 0))["url"]
        if item["url"]:
            media_items.append(item)

    metrics = post.get("public_metrics", {})
    return {
        "id": post["id"],
        "text": post.get("text", ""),
        "created_at": post.get("created_at"),
        "url": f"https://x.com/{user.username}/status/{post['id']}",
        "author": {
            "username": user.username,
            "name": user.display_name,
            "profile_image_url": user.profile_image_url,
            "verified": user.verified,
        },
        "metrics": {
            "replies": metrics.get("reply_count", 0),
            "reposts": metrics.get("retweet_count", 0),
            "likes": metrics.get("like_count", 0),
            "quotes": metrics.get("quote_count", 0),
            "views": metrics.get("impression_count", 0),
        },
        "media": media_items,
    }
