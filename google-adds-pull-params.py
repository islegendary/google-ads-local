import json
import logging
from datetime import datetime, timedelta, timezone
from collections import deque


# Third-party libraries for Google Ads API
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as GoogleCredentials
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
try:
    from google_ads_config import GOOGLE_ADS_CONFIG
except ImportError:
    print("Error: A google_ads_config.py file with a GOOGLE_ADS_CONFIG dictionary is required.")
    exit()

REQUIRED_FIELDS = [
    "developer_token", "client_id", "client_secret",
    "refresh_token", "login_customer_id"
]

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("grpc").setLevel(logging.WARNING)
logger = logging.getLogger()

# --- Functions ---

def build_client_with_refresh() -> GoogleAdsClient:
    """Builds and returns an authenticated GoogleAdsClient."""
    creds = GOOGLE_ADS_CONFIG
    missing = [field for field in REQUIRED_FIELDS if not creds.get(field)]
    if missing:
        raise ValueError(f"Missing required Google Ads credentials: {', '.join(missing)}")

    token_creds = GoogleCredentials(
        token=None, refresh_token=creds['refresh_token'],
        token_uri='https://oauth2.googleapis.com/token',
        client_id=creds['client_id'], client_secret=creds['client_secret'],
        scopes=["https://www.googleapis.com/auth/adwords"]
    )

    if not token_creds.valid or token_creds.expired:
        logger.info("Refreshing access token...")
        token_creds.refresh(Request())

    config = {
        "developer_token": creds["developer_token"],
        "client_id": creds["client_id"], "client_secret": creds["client_secret"],
        "refresh_token": token_creds.refresh_token,
        "login_customer_id": str(creds["login_customer_id"]).replace("-", ""),
        "use_proto_plus": True,
    }
    
    return GoogleAdsClient.load_from_dict(config, version="v19")

def get_full_account_hierarchy(client: GoogleAdsClient, manager_id: str) -> set[str]:
    """
    Performs a recursive traversal of the account hierarchy to find all
    client accounts (non-manager accounts).
    """
    googleads_service = client.get_service("GoogleAdsService")
    manager_ids_to_process = deque([manager_id])
    processed_manager_ids = {manager_id}
    client_customer_ids = set()

    logger.info("Beginning recursive search of the account hierarchy...")

    while manager_ids_to_process:
        current_manager_id = manager_ids_to_process.popleft()
        
        logger.info(
            f"-> Searching under manager {current_manager_id}. "
            f"(Queue size: {len(manager_ids_to_process)})"
        )
        
        query = """
            SELECT
                customer_client.id,
                customer_client.manager
            FROM customer_client
            WHERE customer_client.status = 'ENABLED'
        """
        
        try:
            response_stream = googleads_service.search_stream(
                customer_id=current_manager_id, query=query
            )
            
            for batch in response_stream:
                for row in batch.results:
                    customer = row.customer_client
                    customer_id_str = str(customer.id)

                    if customer.manager:
                        if customer_id_str not in processed_manager_ids:
                            processed_manager_ids.add(customer_id_str)
                            manager_ids_to_process.append(customer_id_str)
                    else:
                        client_customer_ids.add(customer_id_str)

        except GoogleAdsException as e:
            logger.warning(
                f"Could not access hierarchy under manager {current_manager_id}. "
                f"Skipping this branch. Reason: {e.failure.errors[0].message}"
            )
            continue
            
    return client_customer_ids

def query_clicks_for_customer(client: GoogleAdsClient, customer_id: str, query_date: str) -> list[dict]:
    """
    Queries the click_view for a single customer and a single date with a minimal set of fields.
    Handles API errors gracefully, allowing the main script to continue.
    """
    AuthorizationError = client.get_type("AuthorizationErrorEnum").AuthorizationError
    service = client.get_service("GoogleAdsService")
    
    query = f"""
        SELECT 
            click_view.gclid, 
            campaign.id, 
            ad_group.id,
            segments.date
        FROM click_view
        WHERE segments.date = '{query_date}'
    """
    
    results = []
    try:
        response = service.search(customer_id=customer_id, query=query)
        
        processed_rows = list(response)
        if processed_rows:
             logger.info(f"Successfully retrieved {len(processed_rows)} rows for customer {customer_id}.")
             for row in processed_rows:
                results.append({
                    "gclid": row.click_view.gclid,
                    "campaign_id": row.campaign.id,
                    "ad_group_id": row.ad_group.id,
                    "timestamp": row.segments.date,
                    "customer_id": customer_id,
                })
        else:
            logger.info(f"Query successful for customer {customer_id}, but it returned no data for the specified date.")

    except GoogleAdsException as e:
        for error in e.failure.errors:
            if error.error_code.authorization_error == AuthorizationError.USER_PERMISSION_DENIED:
                # Silently ignore permission errors as the user may not have access to all accounts.
                logger.debug(f"Permission denied for customer {customer_id}. Skipping.")
                return []
        # Log other, unexpected errors.
        logger.warning(f"Could not query customer {customer_id}. Reason: {e.failure.errors[0].message}")
        
    return results


def main():
    """Main execution function to orchestrate the entire process."""
    try:
        client = build_client_with_refresh()
        login_cid = str(GOOGLE_ADS_CONFIG["login_customer_id"]).replace("-", "")
    except (ValueError, GoogleAdsException) as e:
        logger.error(f"Failed to initialize Google Ads client. Please check credentials. Error: {e}")
        return

    query_date = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    logger.info(f"Starting job to query click data for date: {query_date}")

    all_data = []

    try:
        # Step 1: Get the definitive list of all client accounts in the entire hierarchy.
        customer_ids_to_query = get_full_account_hierarchy(client, login_cid)
        logger.info(
            f"Hierarchy scan complete. Found {len(customer_ids_to_query)} total client accounts. "
            f"Now querying each for click data..."
        )

        # Step 2: Loop through each account and attempt to query it.
        for i, cid in enumerate(sorted(list(customer_ids_to_query))):
            if (i + 1) % 50 == 0:
                logger.info(f"Query progress: {i + 1} of {len(customer_ids_to_query)} accounts...")
            
            data = query_clicks_for_customer(client, cid, query_date)
            if data:
                all_data.extend(data)
        
        # Step 3: Process the results.
        if not all_data:
            logger.info("Job finished. No click data was found for any accessible accounts for the specified date.")
            return

        # Step 4: Write the collected data to a timestamped JSON file.
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
        filename = f"google_ads_clicks_{ts}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4)

        logger.info(f"Success! Wrote {len(all_data)} click records to local file: {filename}")

    except Exception as e:
        logger.error(f"An unexpected error occurred during execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

