# google-ads-local
This repository contains a small example for collecting click performance data
from the Google Ads API and storing it in a JSON file. The script uses
credentials provided via environment variables so that secrets do not need to be
checked into source control.

The easiest way to supply these variables locally is by creating a `.env` file
in the project root. The script automatically loads this file when present using
`python-dotenv`.

Example `.env` file:

```bash
GOOGLE_ADS_DEVELOPER_TOKEN=your-token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
GOOGLE_ADS_CLIENT_ID=your-client-id
GOOGLE_ADS_CLIENT_SECRET=your-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
```

## Required environment variables

- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID` – manager account ID without hyphens
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`

Optional variables:

- `GOOGLE_ADS_USE_PROTO_PLUS` – defaults to `True`
- `GOOGLE_ADS_ACCESS_TOKEN`

Install dependencies with `pip install -r requirements.txt` and then run the
script:

```bash
python google_ads_parameters.py
```

The script retrieves click information for the previous UTC day from every
account that your manager has access to. The collected records are written to a
JSON file named `google_ads_clicks_<timestamp>.json` in the working directory.

## Troubleshooting

If the script logs an error similar to:

```
User doesn't have permission to access customer. Note: If you're accessing a client customer, the manager's customer id must be set in the 'login-customer-id' header.
```
Sample script terminal output:
2025-06-24 12:05:25,079 - INFO - Refreshing access token...
2025-06-24 12:05:26,722 - INFO - Starting job to query click data for date: 2025-06-23
2025-06-24 12:05:28,348 - INFO - Beginning recursive search of the account hierarchy...
2025-06-24 12:05:28,348 - INFO - -> Searching under manager 5735735731. (Queue size: 0)
2025-06-24 12:05:28,938 - INFO - Hierarchy scan complete. Found 90 total client accounts. Now querying each for click data...
2025-06-24 12:05:31,316 - INFO - Query successful for customer 5736374761, but it returned no data for the specified date.
2025-06-24 12:05:31,949 - INFO - Successfully retrieved 69 rows for customer 8773573579.

ensure the environment variable `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is set to the numeric ID of the manager account **without hyphens** and that the manager has permission to access the client accounts.


