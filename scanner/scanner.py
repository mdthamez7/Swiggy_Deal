import os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from config.categories import CATEGORIES
from config.locations import LOCATIONS
from config.settings import (MAX_LOCATION_WORKERS, MAX_CATEGORY_WORKERS, MAX_PAGES, DELAY, LOOKBACK, MIN_HISTORY, PREVIOUS_LOW_DROP, STABLE_MRP_DROP, MRP_TOLERANCE, COOLDOWN, env_json)
from database.price_history import PriceHistory
from scanner.deal_rules import evaluate
from swiggy.client import MCPClient, unwrap_tool_result
from swiggy.address_resolver import resolve_targets
load_dotenv()
DB_PATH=Path(os.getenv('PRICE_DB_PATH','data/price_history.db'))

def key(t): return f"{t['state']}|{t['city']}|{t['pincode']}"
def extract_products(raw):
    data=raw.get('data',raw) if isinstance(raw,dict) else {}
    products=data.get('products',[]) if isinstance(data,dict) else []
    out=[]
    for p in products:
        pid=str(p.get('productId') or ''); parent=str(p.get('parentProductId') or ''); name=str(p.get('displayName') or ''); brand=str(p.get('brand') or '')
        for v in p.get('variations',[]) or []:
            sid=str(v.get('skuId') or ''); po=v.get('price') or {}; mrp=po.get('mrp'); price=po.get('offerPrice')
            if not pid or not sid or price is None: continue
            try: mrp=float(mrp) if mrp is not None else None; price=float(price)
            except (TypeError,ValueError): continue
            out.append({'product_id':pid,'parent_product_id':parent,'sku_id':sid,'name':name,'brand':brand,'pack':str(v.get('quantityDescription') or v.get('displayName') or ''),'mrp':mrp,'price':price,'in_stock':bool(v.get('isInStockAndAvailable',p.get('inStock',False))),'url':v.get('productUrl') or p.get('productUrl'),'key':f'{pid}:{sid}'})
    return out

def search_category(mcp,address_id,query):
    offset=0
    for page in range(MAX_PAGES):
        raw=unwrap_tool_result(mcp.call_tool('search_products',{'addressId':address_id,'query':query,'offset':offset}))
        yield raw
        data=raw.get('data',raw) if isinstance(raw,dict) else {}
        nxt=data.get('nextOffset') if isinstance(data,dict) else None
        if nxt in (None,'',offset): break
        try: offset=int(nxt)
        except (TypeError,ValueError): break
        if DELAY: time.sleep(DELAY)

def scan_target(target,address_id):
    db=PriceHistory(DB_PATH)
    target_key=key(target); raw_products=[]; errors=[]; started=time.time()
    def one(category):
        mcp=MCPClient(); found=[]
        try:
            mcp.initialize()
            try: mcp.initialized()
            except Exception: pass
            for raw in search_category(mcp,address_id,category):
                for p in extract_products(raw):
                    found.append((category,p))
        except Exception as e:
            errors.append({'state':target['state'],'city':target['city'],'pincode':target['pincode'],'category':category,'error':str(e)})
        finally:
            mcp.close()
        return found
    try:
        with ThreadPoolExecutor(max_workers=MAX_CATEGORY_WORKERS) as pool:
            futures={pool.submit(one,c):c for c in CATEGORIES}
            for fut in as_completed(futures): raw_products.extend(fut.result())
        unique={}
        for category,p in raw_products:
            unique.setdefault(p['key'],(category,p))
        rows=[]; deals=[]
        for category,p in unique.values():
            hist=db.history(p['product_id'],p['sku_id'],target_key,LOOKBACK)
            verdict=evaluate(p['price'],p['mrp'],hist,MIN_HISTORY,PREVIOUS_LOW_DROP,STABLE_MRP_DROP,MRP_TOLERANCE)
            now=datetime.now(timezone.utc).isoformat()
            rows.append((now,target_key,address_id,target['state'],target['city'],target['pincode'],category,p['product_id'],p['sku_id'],p['name'],p['brand'],p['pack'],p['mrp'],p['price'],int(p['in_stock']),p['url']))
            if verdict['is_deal'] and p['in_stock'] and db.can_alert(p['product_id'],p['sku_id'],target_key,COOLDOWN):
                deals.append({**target,**p,'category':category,'previous_low':verdict['previous_low'],'typical':verdict['typical'],'discount':verdict['discount'],'reasons':verdict['reasons']})
        db.save_many(rows)
        db.mark_alert_many([(d['product_id'],d['sku_id'],target_key) for d in deals])
        return {'target':target,'address_id':address_id,'products':len(rows),'deals':deals,'errors':errors,'seconds':time.time()-started}
    finally: db.close()

def print_summary(results,unmapped):
    print('\n'+'='*78); print('LOOTDEAL SCAN SUMMARY'); print('='*78)
    for r in sorted(results,key=lambda x:(x['target']['state'],x['target']['city'],x['target']['pincode'])):
        t=r['target']; print(f"{t['state']:<18} {t['city']:<18} {t['pincode']} | products={r['products']:<5} deals={len(r['deals']):<4} {r['seconds']:.1f}s")
    if unmapped:
        print('\nTARGETS WITHOUT A REAL SWIGGY ADDRESS ID:')
        for t in unmapped: print(f"- {t['state']} / {t['city']} / {t['pincode']}")

def run():
    print('='*78); print('LOOTDEAL - SWIGGY INSTAMART GITHUB SCANNER'); print('='*78)
    print(f'Locations configured : {len(LOCATIONS)}'); print(f'Categories           : {len(CATEGORIES)}'); print(f'Location workers     : {MAX_LOCATION_WORKERS}'); print(f'Category workers     : {MAX_CATEGORY_WORKERS}'); print('Mode                 : NON-INTERACTIVE')
    # Resolve target city/pincode against the authenticated account's real
    # saved Swiggy addresses on every run. No address IDs are stored in the
    # repository and no IDs are guessed or generated.
    mapped, unmapped = resolve_targets(LOCATIONS, token=os.getenv('SWIGGY_ACCESS_TOKEN'))
    print(f'Resolved targets     : {len(mapped)}')
    print(f'Unresolved targets   : {len(unmapped)}')
    if not mapped:
        raise RuntimeError(
            'No target locations matched a real saved Swiggy address. '
            'Add the target location to the authenticated Swiggy account, '
            'or remove that target from TARGET_LOCATIONS_JSON.'
        )
    started=time.time(); results=[]
    with ThreadPoolExecutor(max_workers=min(MAX_LOCATION_WORKERS,len(mapped))) as pool:
        futures={pool.submit(scan_target,t,aid):t for t,aid in mapped}
        for fut in as_completed(futures):
            t=futures[fut]
            try:
                r=fut.result(); results.append(r); print(f"DONE {t['state']} / {t['city']} {t['pincode']} -> {r['products']} products, {len(r['deals'])} deals")
            except Exception as e: print(f"FAILED {t['state']} / {t['city']} {t['pincode']} -> {e}")
    deals=[d for r in results for d in r['deals']]; errors=[e for r in results for e in r['errors']]
    print_summary(results,unmapped)
    from alerts.email import send_deal_email
    send_deal_email(deals,unmapped,errors)
    print(f'\nTotal elapsed: {time.time()-started:.1f}s')
    return 0
if __name__=='__main__': run()
