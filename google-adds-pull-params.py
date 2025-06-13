import json
import logging
from datetime import datetime, timedelta, timezone

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as GoogleCredentials

# Import your credentials
from google_ads_config import GOOGLE_ADS_CONFIG

REQUIRED_FIELDS = [
    "developer_token",
    "client_id",
    "client_secret",
    "refresh_token",
    "login_customer_id",
]

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# --- Google Ads Client Builder ---
def build_client_with_refresh() -> GoogleAdsClient:
    """Return an authenticated GoogleAdsClient refreshing OAuth as needed."""
    creds = GOOGLE_ADS_CONFIG

    missing = [field for field in REQUIRED_FIELDS if not creds.get(field)]
    if missing:
        raise ValueError(
            f"Missing required Google Ads credentials: {', '.join(missing)}"
        )

    token_creds = GoogleCredentials(
        token=None,
        refresh_token=creds['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        scopes=["https://www.googleapis.com/auth/adwords"]
    )

    if not token_creds.valid or token_creds.expired:
        logger.info("Refreshing access token...")
        token_creds.refresh(Request())

    config = {
        "developer_token": creds["developer_token"],
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": token_creds.refresh_token,
        "login_customer_id": int(creds["login_customer_id"]),
        "use_proto_plus": creds.get("use_proto_plus", True),
        "endpoint": "googleads.googleapis.com"
    }

    return GoogleAdsClient.load_from_dict(config, version="v20")

# --- Google Ads Operations ---
def list_customer_ids(client: GoogleAdsClient) -> list:
    try:
        service = client.get_service("CustomerService")
        response = service.list_accessible_customers()
        return [res.replace("customers/", "") for res in response.resource_names]
    except Exception as e:
        logger.error(f"⚠️ Failed to list accessible customers: {e}")
        raise

def query_clicks(client, customer_id, start_date, end_date) -> list:
    service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT click_view.gclid, campaign.id, segments.date, ad_group.id
        FROM click_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
    """
    results = []
    try:
        response = service.search(customer_id=customer_id, query=query)
        for row in response:
            results.append({
                "gclid": row.click_view.gclid,
                "campaign_id": row.campaign.id,
                "timestamp": row.segments.date.value,
                "customer_id": customer_id,
            })
    except GoogleAdsException as e:
        logger.warning(f"Google Ads error for {customer_id}: {e}")
    return results

# --- Main Runner ---
def main():
    client = build_client_with_refresh()

    start_date = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    end_date = datetime.now(timezone.utc).date().isoformat()
    logger.info(f"Running for window: {start_date} → {end_date}")

    all_data = []

    try:
        for cid in list_customer_ids(client):
            logger.info(f"📡 Querying customer: {cid}")
            data = query_clicks(client, cid, start_date, end_date)
            all_data.extend(data)

        if not all_data:
            logger.info("No data returned.")
            return

        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
        filename = f"clicks_{ts}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2)

        logger.info(f"✅ Wrote {len(all_data)} records to local file: {filename}")

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise

# --- Run It ---
if __name__ == "__main__":
    main()
