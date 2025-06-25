# google_ads_config.py
"""Configuration helpers for authenticating with Google Ads API.

This module reads credentials from environment variables so secret values do
not need to be committed to source control.  Each variable mirrors the fields
expected by :class:`google.ads.googleads.client.GoogleAdsClient`.

Required environment variables:

``GOOGLE_ADS_DEVELOPER_TOKEN``      Developer token issued by Google.
``GOOGLE_ADS_LOGIN_CUSTOMER_ID``    Manager account ID without hyphens.
``GOOGLE_ADS_CLIENT_ID``            OAuth2 client ID.
``GOOGLE_ADS_CLIENT_SECRET``        OAuth2 client secret.
``GOOGLE_ADS_REFRESH_TOKEN``        OAuth2 refresh token.

``GOOGLE_ADS_USE_PROTO_PLUS`` and ``GOOGLE_ADS_ACCESS_TOKEN`` are optional and
default to ``True`` and an empty string respectively.
"""

import os

GOOGLE_ADS_CONFIG = {
    "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
    "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", ""),
    "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID", ""),
    "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET", ""),
    "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN", ""),
    "use_proto_plus": os.getenv("GOOGLE_ADS_USE_PROTO_PLUS", "True").lower() in (
        "true",
        "1",
        "yes",
    ),
    "access_token": os.getenv("GOOGLE_ADS_ACCESS_TOKEN", ""),
}
