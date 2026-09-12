import os, json
required=['SWIGGY_ACCESS_TOKEN','SWIGGY_ADDRESS_MAP_JSON']
missing=[x for x in required if not os.getenv(x,'').strip()]
if missing: raise SystemExit('Missing required GitHub Secrets: '+', '.join(missing))
try: locations=json.loads(os.getenv('TARGET_LOCATIONS_JSON','')) if os.getenv('TARGET_LOCATIONS_JSON','').strip() else []
except Exception as e: raise SystemExit(f'TARGET_LOCATIONS_JSON is invalid JSON: {e}')
try: amap=json.loads(os.getenv('SWIGGY_ADDRESS_MAP_JSON',''))
except Exception as e: raise SystemExit(f'SWIGGY_ADDRESS_MAP_JSON is invalid JSON: {e}')
if not isinstance(amap,dict): raise SystemExit('SWIGGY_ADDRESS_MAP_JSON must be a JSON object.')
print(f'Configuration OK. GitHub targets variable contains {len(locations)} locations; address map contains {len(amap)} mappings.')
