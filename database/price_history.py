import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

class PriceHistory:
    def __init__(self, db_path):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, observed_at TEXT NOT NULL,
            target_key TEXT NOT NULL, address_id TEXT NOT NULL, state TEXT NOT NULL,
            city TEXT NOT NULL, pincode TEXT NOT NULL, category TEXT NOT NULL,
            product_id TEXT NOT NULL, sku_id TEXT NOT NULL, product_name TEXT NOT NULL,
            brand TEXT, pack TEXT, mrp REAL, price REAL NOT NULL, in_stock INTEGER NOT NULL,
            product_url TEXT)""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_history_product ON observations(product_id,sku_id,target_key,observed_at)")
        self.db.execute("""CREATE TABLE IF NOT EXISTS alerts (
            product_id TEXT NOT NULL, sku_id TEXT NOT NULL, target_key TEXT NOT NULL,
            last_alert_at TEXT NOT NULL, PRIMARY KEY(product_id,sku_id,target_key))""")
        self.db.commit()

    def history(self, product_id, sku_id, target_key, lookback_days):
        cutoff=(datetime.now(timezone.utc)-timedelta(days=lookback_days)).isoformat()
        return self.db.execute("SELECT price,mrp FROM observations WHERE product_id=? AND sku_id=? AND target_key=? AND observed_at>=? ORDER BY observed_at DESC",(product_id,sku_id,target_key,cutoff)).fetchall()
    def save_many(self, rows):
        self.db.executemany("""INSERT INTO observations
        (observed_at,target_key,address_id,state,city,pincode,category,product_id,sku_id,product_name,brand,pack,mrp,price,in_stock,product_url)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows); self.db.commit()
    def can_alert(self, product_id, sku_id, target_key, cooldown_hours):
        row=self.db.execute("SELECT last_alert_at FROM alerts WHERE product_id=? AND sku_id=? AND target_key=?",(product_id,sku_id,target_key)).fetchone()
        if not row:return True
        return datetime.now(timezone.utc)-datetime.fromisoformat(row[0]) >= timedelta(hours=cooldown_hours)
    def mark_alert_many(self, keys):
        now=datetime.now(timezone.utc).isoformat()
        self.db.executemany("""INSERT INTO alerts(product_id,sku_id,target_key,last_alert_at) VALUES(?,?,?,?)
        ON CONFLICT(product_id,sku_id,target_key) DO UPDATE SET last_alert_at=excluded.last_alert_at""",[(a,b,c,now) for a,b,c in keys]); self.db.commit()
    def close(self): self.db.close()
