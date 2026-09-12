import json
import os
from dotenv import load_dotenv
load_dotenv()

def env_int(name, default):
    try: return int(os.getenv(name, str(default)))
    except ValueError: return default

def env_float(name, default):
    try: return float(os.getenv(name, str(default)))
    except ValueError: return default

def env_json(name, default):
    raw = os.getenv(name, '').strip()
    if not raw: return default
    try: return json.loads(raw)
    except json.JSONDecodeError as e: raise RuntimeError(f'{name} is not valid JSON: {e}')

DEFAULT_LOCATIONS = [
 {'state':'Tamil Nadu','city':'Madurai','pincode':'625016'}, {'state':'Tamil Nadu','city':'Madurai','pincode':'625010'}, {'state':'Tamil Nadu','city':'Madurai','pincode':'625001'},
 {'state':'Tamil Nadu','city':'Chennai','pincode':'600096'}, {'state':'Tamil Nadu','city':'Chengalpattu','pincode':'603002'},
 {'state':'Karnataka','city':'Bengaluru','pincode':'560102'}, {'state':'Tamil Nadu','city':'Coimbatore','pincode':'641001'}, {'state':'Tamil Nadu','city':'Tiruchirappalli','pincode':'620001'}, {'state':'Tamil Nadu','city':'Salem','pincode':'636001'}, {'state':'Tamil Nadu','city':'Tirunelveli','pincode':'627001'},
 {'state':'Karnataka','city':'Mysuru','pincode':'570001'}, {'state':'Karnataka','city':'Mangaluru','pincode':'575001'}, {'state':'Kerala','city':'Kochi','pincode':'682001'}, {'state':'Kerala','city':'Thiruvananthapuram','pincode':'695001'}, {'state':'Kerala','city':'Kozhikode','pincode':'673001'},
 {'state':'Telangana','city':'Hyderabad','pincode':'500001'}, {'state':'Andhra Pradesh','city':'Vijayawada','pincode':'520001'}, {'state':'Andhra Pradesh','city':'Visakhapatnam','pincode':'530001'},
 {'state':'Maharashtra','city':'Mumbai','pincode':'400001'}, {'state':'Maharashtra','city':'Pune','pincode':'411001'}, {'state':'Maharashtra','city':'Nagpur','pincode':'440001'}, {'state':'Gujarat','city':'Ahmedabad','pincode':'380001'},
 {'state':'Delhi','city':'New Delhi','pincode':'110001'}, {'state':'Haryana','city':'Gurugram','pincode':'122001'}, {'state':'Uttar Pradesh','city':'Noida','pincode':'201301'}, {'state':'Uttar Pradesh','city':'Lucknow','pincode':'226001'},
 {'state':'West Bengal','city':'Kolkata','pincode':'700001'}, {'state':'Odisha','city':'Bhubaneswar','pincode':'751001'}, {'state':'Assam','city':'Guwahati','pincode':'781001'}, {'state':'Jharkhand','city':'Ranchi','pincode':'834001'}, {'state':'Bihar','city':'Patna','pincode':'800001'},
 {'state':'Rajasthan','city':'Jaipur','pincode':'302001'}, {'state':'Madhya Pradesh','city':'Indore','pincode':'452001'}, {'state':'Madhya Pradesh','city':'Bhopal','pincode':'462001'}, {'state':'Chandigarh','city':'Chandigarh','pincode':'160001'}, {'state':'Puducherry','city':'Puducherry','pincode':'605001'},
]
LOCATIONS = env_json('TARGET_LOCATIONS_JSON', DEFAULT_LOCATIONS)
CATEGORIES = env_json('CATEGORY_QUERIES_JSON', None)
MAX_LOCATION_WORKERS = max(1, env_int('MAX_LOCATION_WORKERS', 5))
MAX_CATEGORY_WORKERS = max(1, env_int('MAX_CATEGORY_WORKERS', 4))
MAX_PAGES = max(1, env_int('MAX_PAGES_PER_CATEGORY', 3))
DELAY = max(0.0, env_float('REQUEST_DELAY_SECONDS', 0.2))
LOOKBACK = max(1, env_int('HISTORY_LOOKBACK_DAYS', 90))
MIN_HISTORY = max(1, env_int('MIN_HISTORY_OBSERVATIONS', 2))
PREVIOUS_LOW_DROP = env_float('PREVIOUS_LOW_DROP', 0.20)
STABLE_MRP_DROP = env_float('STABLE_MRP_MIN_DROP', 0.20)
MRP_TOLERANCE = env_float('MRP_STABLE_TOLERANCE', 0.05)
COOLDOWN = max(0, env_int('ALERT_COOLDOWN_HOURS', 24))
