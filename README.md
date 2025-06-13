# google-ads-local
This repository contains a small example for collecting click performance data
from the Google Ads API and storing it in a JSON file. The script uses
credentials provided via environment variables so that secrets do not need to be
checked into source control.

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
python google-adds-pull-params.py
```


