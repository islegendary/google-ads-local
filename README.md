````markdown
# Google Ads Return Click Parameters

This repository provides a lightweight solution for companies using Google Search Ads to improve attribution reporting. It captures critical click-level data from the Google Ads API, enriching web sessions that contain `gclid` parameters with campaign, ad group, and ad network details.

## Key Features

- Traverses Google Ads account hierarchies (MCC)
- Queries click performance data across all accessible client accounts
- Securely handles OAuth2 authentication and token refresh via environment variables
- Stores detailed, timestamped click data in JSON files for downstream use

## Integration Flexibility

The local JSON output can be immediately added to Page and Event tracking when users visit from Google Search Ads. The solution is easily adaptable to write directly to platforms like:

- Amazon DynamoDB
- Amazon Redshift
- Google BigQuery
- Azure Data Lake
- Snowflake
- Databricks Delta Lake

This flexibility allows seamless integration into larger pipelines for real-time or batch processing, advanced reporting, cross-channel attribution, and user-level personalization.

## Setup Instructions

### Environment Configuration

The easiest way to supply credentials locally is by creating a `.env` file in the project root. The script automatically loads this file using `python-dotenv`.

Example `.env` file:
```bash
GOOGLE_ADS_DEVELOPER_TOKEN=your-token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
GOOGLE_ADS_CLIENT_ID=your-client-id
GOOGLE_ADS_CLIENT_SECRET=your-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
````

### Required Environment Variables

* `GOOGLE_ADS_DEVELOPER_TOKEN`
* `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (manager account ID without hyphens)
* `GOOGLE_ADS_CLIENT_ID`
* `GOOGLE_ADS_CLIENT_SECRET`
* `GOOGLE_ADS_REFRESH_TOKEN`

### Optional Variables

* `GOOGLE_ADS_USE_PROTO_PLUS` (defaults to `True`)
* `GOOGLE_ADS_ACCESS_TOKEN`

### Install and Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the script:

```bash
python google_ads_parameters.py
```

The script retrieves click information for the previous UTC day from every account your manager has access to. Results are written to:

```text
google_ads_clicks_<timestamp>.json
```

## Troubleshooting

If you see this error:

```text
User doesn't have permission to access customer. Note: If you're accessing a client customer, the manager's customer id must be set in the 'login-customer-id' header.
```

Ensure that:

* `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is set to the numeric ID of the manager account **without hyphens**
* The manager account has the proper permissions to access the client accounts

## Example Terminal Output

```text
2025-06-24 12:05:25,079 - INFO - Refreshing access token...
2025-06-24 12:05:26,722 - INFO - Starting job to query click data for date: 2025-06-23
2025-06-24 12:05:28,348 - INFO - Beginning recursive search of the account hierarchy...
2025-06-24 12:05:28,348 - INFO - -> Searching under manager 5735735731. (Queue size: 0)
2025-06-24 12:05:28,938 - INFO - Hierarchy scan complete. Found 90 total client accounts. Now querying each for click data...
2025-06-24 12:05:31,316 - INFO - Query successful for customer 5736374761, but it returned no data for the specified date.
2025-06-24 12:05:31,949 - INFO - Successfully retrieved 69 rows for customer 8773573579.
```
