# LootDeal — GitHub Actions setup

## Important Swiggy limitation

Swiggy Instamart `search_products` requires a real `addressId` from `get_addresses`; a pincode alone is not accepted. Swiggy's MCP documentation also instructs clients to obtain the address ID from `get_addresses`. Therefore this package keeps your target city/PIN list in GitHub Variables, but it **will only scan a target when you provide a real Swiggy address ID mapping for that target**. It will never invent an ID or create a fake address. See the official docs: https://mcp.swiggy.com/builders/docs/reference/instamart/get_addresses/ and https://mcp.swiggy.com/builders/docs/reference/instamart/search_products/.

This is the only reliable way to honor both requirements: no fake addresses and no user prompts during scheduled scans.

## GitHub setup

### 1. Create a repository

Create a private GitHub repository and upload the contents of this package to its root.

### 2. Repository Variables

Go to **Settings → Secrets and variables → Actions → Variables** and create:

`SWIGGY_IM_MCP_URL`
```
https://mcp.swiggy.com/im
```

`MAX_LOCATION_WORKERS`
```
5
```

`MAX_CATEGORY_WORKERS`
```
4
```

`MAX_PAGES_PER_CATEGORY`
```
3
```

`REQUEST_DELAY_SECONDS`
```
0.2
```

`HISTORY_LOOKBACK_DAYS`
```
90
```

`MIN_HISTORY_OBSERVATIONS`
```
2
```

`PREVIOUS_LOW_DROP`
```
0.20
```

`STABLE_MRP_MIN_DROP`
```
0.20
```

`MRP_STABLE_TOLERANCE`
```
0.05
```

`ALERT_COOLDOWN_HOURS`
```
24
```

`SMTP_HOST`
```
smtp.gmail.com
```

`SMTP_PORT`
```
587
```

`ALERT_TO`
```
your-alert-email@example.com
```

### 3. Target locations variable

Create `TARGET_LOCATIONS_JSON` with the locations you want scanned. The package has your requested defaults, but putting the list in GitHub makes it editable without code changes.

Example:
```json
[{"state":"Tamil Nadu","city":"Madurai","pincode":"625016"},{"state":"Tamil Nadu","city":"Madurai","pincode":"625010"},{"state":"Tamil Nadu","city":"Madurai","pincode":"625001"},{"state":"Tamil Nadu","city":"Chennai","pincode":"600096"},{"state":"Tamil Nadu","city":"Chengalpattu","pincode":"603002"},{"state":"Karnataka","city":"Bengaluru","pincode":"560102"}]
```

Use the full list from `config/settings.py` as the starting list. You can add/remove cities later.

### 4. Category variable (optional)

Create `CATEGORY_QUERIES_JSON` if you want GitHub to own the category list. It must be a JSON array of search strings. If omitted, the built-in 100+ category/search-term list is used.

### 5. GitHub Secrets

Go to **Settings → Secrets and variables → Actions → Secrets**.

Create:

`SWIGGY_ACCESS_TOKEN`

This is the current access token from the successful Swiggy OAuth login.

`SWIGGY_ADDRESS_MAP_JSON`

This is a JSON object mapping each target key to the **real Swiggy address ID** for that target. Example:
```json
{"Tamil Nadu|Madurai|625016":"addr_abc123","Karnataka|Bengaluru|560102":"addr_xyz789"}
```

Never invent IDs. The key format is exactly:
`STATE|CITY|PINCODE`

`SMTP_USER`

Your Gmail address (or SMTP username).

`SMTP_PASSWORD`

For Gmail, use a Gmail App Password rather than the normal account password.

### 6. Build the address map

Because Swiggy requires real saved address IDs, use the already-working local OAuth package once to retrieve them:

```powershell
python -m diagnostics.export_addresses
```

It prints the real saved address objects and their IDs. Add only the mappings that genuinely correspond to your target locations to `SWIGGY_ADDRESS_MAP_JSON`.

**Do not create fake street addresses and do not guess IDs.**

### 7. Token lifetime

Swiggy documents access tokens as lasting 5 days and says refresh-token issuance is not wired in v1.0. When the token expires/revokes, re-authorization is required. Therefore this GitHub build cannot promise permanent unattended OAuth forever with the current Swiggy contract. Re-run the one-time local OAuth flow and replace `SWIGGY_ACCESS_TOKEN` when needed. Official docs: https://mcp.swiggy.com/builders/docs/start/authenticate/

### 8. First test

Go to **Actions → LootDeal Scanner → Run workflow**.

Watch the log. It should show:
- configured targets
- mapped/unmapped targets
- parallel location workers
- products found
- deals found
- total elapsed time

### 9. Enable the 20-minute schedule

The workflow already contains:
```yaml
schedule:
  - cron: '*/20 * * * *'
```

It also has `workflow_dispatch` for manual runs.

The concurrency group prevents two scans from running simultaneously.

### 10. Price history

GitHub runners are ephemeral. The workflow restores the SQLite price-history database from the previous GitHub Actions cache and saves an updated cache after each run. This allows the stable-MRP / historical-price rules to work across runs.

If the cache is ever evicted, the scanner will rebuild its baseline from new observations.

## Deal rules

A product can trigger when:
- MRP discount is at least 20%, with stronger 50%, 80% and 90% tiers also reported;
- current price is at least 20% below its previous observed low after the minimum history requirement;
- MRP is stable within the configured tolerance and the current price is at least 20% below its historical typical price.

Email alerts are cooldown-protected so the same SKU/location does not generate an alert every 20 minutes.

## Safety

The scanner only reads addresses and searches products. It does not add to cart, checkout, pay, or place orders.
