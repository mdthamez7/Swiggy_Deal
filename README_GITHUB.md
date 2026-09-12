# LootDeal — GitHub Actions setup

## What this version does

This version keeps the scan targets in GitHub Variables and **does not require `SWIGGY_ADDRESS_MAP_JSON`**.

At the start of every run it calls Swiggy `get_addresses`, reads the authenticated account's real saved addresses, and matches each target by city + pincode. The scanner then uses the returned real `addressId` for `search_products`.

It never invents an address ID and never stores an address ID in the repository.

> **Important Swiggy limitation:** `get_addresses` returns saved addresses for the authenticated Swiggy account. A pincode/city is not itself an `addressId`. Therefore a target can only be scanned automatically when that city/pincode exists in a real saved address on the authenticated account. If a target has no matching saved address, it is reported as unresolved and skipped.

## GitHub Secrets

Go to **Settings → Secrets and variables → Actions → Secrets**.

### Required

`SWIGGY_ACCESS_TOKEN`

Your current Swiggy OAuth access token.

### Swiggy MCP endpoint

`SWIGGY_IM_MCP_URL` is optional. If omitted or left blank, the scanner automatically uses `https://mcp.swiggy.com/im`. If you create the GitHub Variable, use the full URL including `https://`.

### Optional email alerts

`SMTP_USER`

`SMTP_PASSWORD`

For Gmail, use an App Password rather than your normal password.

## GitHub Variables

Go to **Settings → Secrets and variables → Actions → Variables**.

### Target locations

Create `TARGET_LOCATIONS_JSON`.

Example:

```json
[{"state":"Tamil Nadu","city":"Madurai","pincode":"625016"},{"state":"Tamil Nadu","city":"Madurai","pincode":"625010"},{"state":"Tamil Nadu","city":"Madurai","pincode":"625001"},{"state":"Tamil Nadu","city":"Chennai","pincode":"600096"},{"state":"Karnataka","city":"Bengaluru","pincode":"560102"}]
```

The package also contains a broader default city list in `config/settings.py` for local runs. For GitHub Actions, set the variable so GitHub is the source of truth.

### Performance variables

Recommended starting values:

```text
MAX_LOCATION_WORKERS=5
MAX_CATEGORY_WORKERS=4
MAX_PAGES_PER_CATEGORY=3
REQUEST_DELAY_SECONDS=0.2
```

The workflow is scheduled every 20 minutes.

## Address resolution

The scanner does **not** use an old locally stored address. Every run performs:

1. `get_addresses`
2. pagination through all saved addresses
3. city + pincode matching against `TARGET_LOCATIONS_JSON`
4. `search_products` using the matching real `addressId`

If you add a new target city, that city must exist as a real saved Swiggy delivery address in the authenticated account before it can be scanned.

Do not invent an `addressId` and do not create a fake street address just to satisfy the scanner.

## 20-minute workflow

`.github/workflows/lootdeal.yml` already contains:

```yaml
schedule:
  - cron: '*/20 * * * *'
```

It also supports **workflow_dispatch** for manual testing.

The workflow uses parallel location workers and parallel category workers to keep the scan fast. The concurrency group prevents overlapping scheduled runs.

## Price history

GitHub runners are temporary. The workflow restores and saves `data/price_history.db` using GitHub Actions cache so historical-price deal rules can continue across runs.

## Token expiry

Swiggy access tokens are time-limited. When the token expires or is revoked, re-run the local OAuth login and replace the `SWIGGY_ACCESS_TOKEN` GitHub Secret.

## Safety

The scanner only reads saved addresses and searches Instamart products. It does not add items to a cart, checkout, pay, or place orders.
