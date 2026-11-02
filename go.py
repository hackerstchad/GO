#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██╗  ██╗██╗     ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗               ║
║   ██║  ██║██║     ██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝               ║
║   ███████║██║     ██████╔╝███████║██║   ██║██╔██╗ ██║█████╗                 ║
║   ██╔══██║██║     ██╔══██╗██╔══██║██║   ██║██║╚██╗██║██╔══╝                 ║
║   ██║  ██║███████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║██║                    ║
║   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝                    ║
║                                                                              ║
║   Phone Intelligence & Identity Resolver                                     ║
║   Advanced OSINT automation for phone numbers                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import re
import json
import time
import random
import hashlib
import argparse
import textwrap
import threading
import subprocess
from datetime import datetime
from urllib.parse import quote, unquote, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

# ────────────────────────────────
# TRY TO IMPORT OPTIONAL DEPENDENCIES
# ────────────────────────────────
try:
    import requests
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False
    requests = None

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone
    HAS_PHONENUMBERS = True
except Exception:
    HAS_PHONENUMBERS = False
    phonenumbers = None

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except Exception:
    HAS_BS4 = False
    BeautifulSoup = None

try:
    import lxml
    HAS_LXML = True
except Exception:
    HAS_LXML = False

try:
    import colorama
    colorama.init(autoreset=True)
    HAS_COLORAMA = True
except Exception:
    HAS_COLORAMA = False

# ────────────────────────────────
# GLOBAL CONFIGURATION
# ────────────────────────────────
__version__ = "9.9.9"
__author__ = "HI Intelligence Team"
__script_name__ = "HI"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".hi")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
KEYS_FILE = os.path.join(CONFIG_DIR, "keys.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")
CACHE_DIR = os.path.join(CONFIG_DIR, "cache")
LOG_DIR = os.path.join(CONFIG_DIR, "logs")
EXPORT_DIR = os.path.join(CONFIG_DIR, "exports")

DEFAULT_TIMEOUT = 22
DEFAULT_THREADS = 12
MAX_RETRIES = 3
USER_AGENT_ROTATION = True
ENABLE_CACHE = True
ENABLE_LOG = True
QUIET_MODE = False
VERBOSE_MODE = False

# ────────────────────────────────
# COLOR PALETTE
# ────────────────────────────────
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

# ────────────────────────────────
# UTILITY FUNCTIONS
# ────────────────────────────────
def ensure_dirs():
    for d in [CONFIG_DIR, CACHE_DIR, LOG_DIR, EXPORT_DIR]:
        os.makedirs(d, exist_ok=True)

def load_json(path, default=None):
    if default is None:
        default = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def log_event(message, level="INFO"):
    if not ENABLE_LOG:
        return
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(LOG_DIR, f"hi_{datetime.now().strftime('%Y%m%d')}.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception:
        pass

def print_banner():
    banner = f"""{C.BRIGHT_GREEN}{C.BOLD}
    ██╗  ██╗██╗     ██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗
    ██║  ██║██║     ██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝
    ███████║██║     ██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  
    ██╔══██║██║     ██╔══██╗██╔══██║██║   ██║██║╚██╗██║██╔══╝  
    ██║  ██║███████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║██║     
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     
{C.CYAN}    Phone Intelligence & Identity Resolver v{__version__}{C.RESET}
{C.BRIGHT_GREEN}    ──────────────────────────────────────────────────────{C.RESET}
    """
    print(banner)

def print_centered(text, width=70, char="─", color=C.BRIGHT_GREEN):
    text = f" {text} "
    pad = max(0, width - len(text))
    left = pad // 2
    right = pad - left
    print(f"{color}{char * left}{C.BOLD}{text}{C.RESET}{color}{char * right}{C.RESET}")

def random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Android 14; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0",
    ]
    return random.choice(agents)

def http_session():
    if not HAS_REQUESTS:
        return None
    s = requests.Session()
    s.headers.update({
        "User-Agent": random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    })
    return s

def safe_request(session, url, method="GET", data=None, headers=None, timeout=DEFAULT_TIMEOUT, retries=MAX_RETRIES):
    if session is None:
        return None
    attempt = 0
    while attempt <= retries:
        try:
            if method.upper() == "POST":
                r = session.post(url, data=data, headers=headers, timeout=timeout)
            else:
                r = session.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            attempt += 1
            if attempt > retries:
                log_event(f"Request failed after {retries} retries: {url} -> {e}", "ERROR")
                return None
            time.sleep(0.7 * attempt)
    return None

def normalize_phone(raw):
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 10:
        digits = "33" + digits[1:]
    if len(digits) >= 8 and not digits.startswith("+") and not digits.startswith("00"):
        if not digits.startswith("1") and not digits.startswith("2") and len(digits) <= 12:
            pass
    return digits

def format_international(raw):
    if not HAS_PHONENUMBERS:
        return None
    try:
        x = phonenumbers.parse(raw, None)
        return phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except Exception:
        try:
            x = phonenumbers.parse(raw, "FR")
            return phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except Exception:
            return None

def get_phone_metadata(raw):
    if not HAS_PHONENUMBERS:
        return {}
    try:
        x = phonenumbers.parse(raw, None)
    except Exception:
        try:
            x = phonenumbers.parse(raw, "FR")
        except Exception:
            return {}
    try:
        country = geocoder.description_for_number(x, "en")
    except Exception:
        country = "Unknown"
    try:
        op = carrier.name_for_number(x, "en")
    except Exception:
        op = "Unknown"
    try:
        tz = timezone.time_zones_for_number(x)
    except Exception:
        tz = []
    return {
        "valid": phonenumbers.is_valid_number(x),
        "country": country,
        "country_code": x.country_code,
        "national_number": str(x.national_number),
        "region": phonenumbers.region_code_for_number(x),
        "carrier": op,
        "timezones": tz,
        "type": str(phonenumbers.number_type(x)),
    }

# ────────────────────────────────
# API KEY MANAGEMENT
# ────────────────────────────────
SUPPORTED_APIS = {
    "numverify": {"name": "Numverify", "url": "http://apilayer.net/api/validate", "fields": ["access_key"]},
    "twilio": {"name": "Twilio Lookup", "url": "https://lookups.twilio.com/v1/PhoneNumbers/", "fields": ["account_sid", "auth_token"]},
    "truecaller": {"name": "Truecaller", "url": "https://search5-noneu.truecaller.com/v2/search", "fields": ["authorization"]},
    "synaps": {"name": "Synaps", "url": "", "fields": ["api_key"]},
    "carrierlookup": {"name": "CarrierLookup", "url": "", "fields": ["api_key"]},
}

def load_keys():
    return load_json(KEYS_FILE, {})

def save_keys(keys):
    return save_json(KEYS_FILE, keys)

def prompt_key(api):
    print(f"{C.YELLOW}[>] Configure API key for {SUPPORTED_APIS[api]['name']}{C.RESET}")
    vals = {}
    for field in SUPPORTED_APIS[api]["fields"]:
        try:
            val = input(f"{C.CYAN}    {field}: {C.RESET}").strip()
        except EOFError:
            val = ""
        vals[field] = val
    keys = load_keys()
    keys[api] = vals
    save_keys(keys)
    print(f"{C.GREEN}[+] Saved.{C.RESET}")
    return vals

def get_key(api):
    keys = load_keys()
    if api in keys and keys[api]:
        return keys[api]
    return prompt_key(api)

# ────────────────────────────────
# PROGRESS BAR
# ────────────────────────────────
class ProgressBar:
    def __init__(self, total, width=50, prefix="Progress", suffix="Complete", color=C.BRIGHT_GREEN):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.suffix = suffix
        self.color = color
        self.current = 0
        self.lock = threading.Lock()
        self.start = time.time()

    def update(self, step=1, message=""):
        with self.lock:
            self.current = min(self.total, self.current + step)
            pct = self.current / self.total if self.total else 1
            filled = int(self.width * pct)
            bar = f"{self.color}{'█' * filled}{C.DIM}{'░' * (self.width - filled)}{C.RESET}"
            elapsed = time.time() - self.start
            eta = (elapsed / pct) - elapsed if pct > 0 else 0
            line = f"\r{C.BOLD}{self.prefix}{C.RESET} {bar} {self.color}{pct*100:5.1f}%{C.RESET} {C.CYAN}{self.current}/{self.total}{C.RESET} ETA {eta:04.1f}s {message}"
            sys.stdout.write(line)
            sys.stdout.flush()

    def finish(self, message=""):
        with self.lock:
            sys.stdout.write("\n")
            if message:
                print(f"{self.color}[✓] {message}{C.RESET}")
            sys.stdout.flush()

# ────────────────────────────────
# CACHE MANAGEMENT
# ────────────────────────────────
def cache_key(phone, source):
    h = hashlib.sha256(f"{phone}:{source}".encode("utf-8")).hexdigest()[:32]
    return os.path.join(CACHE_DIR, f"{h}.json")

def read_cache(phone, source):
    if not ENABLE_CACHE:
        return None
    path = cache_key(phone, source)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("expires", 0) > time.time():
                return data.get("payload")
        except Exception:
            pass
    return None

def write_cache(phone, source, payload, ttl=86400):
    if not ENABLE_CACHE:
        return
    path = cache_key(phone, source)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"expires": time.time() + ttl, "payload": payload}, f, ensure_ascii=False)
    except Exception:
        pass

# ────────────────────────────────
# IDENTITY LEAK / OSINT SOURCES
# ────────────────────────────────
class PhoneSource:
    def __init__(self, name, func, enabled=True):
        self.name = name
        self.func = func
        self.enabled = enabled

    def run(self, session, phone, meta):
        try:
            cached = read_cache(phone, self.name)
            if cached is not None:
                return {"source": self.name, "cached": True, "data": cached}
            data = self.func(session, phone, meta)
            if data:
                write_cache(phone, self.name, data)
            return {"source": self.name, "cached": False, "data": data}
        except Exception as e:
            log_event(f"Source {self.name} failed: {e}", "ERROR")
            return {"source": self.name, "error": str(e)}

def source_numverify(session, phone, meta):
    keys = load_keys().get("numverify")
    if not keys or not keys.get("access_key"):
        return {"configured": False, "note": "No API key configured"}
    url = f"{SUPPORTED_APIS['numverify']['url']}?access_key={keys['access_key']}&number={phone}&country_code=&format=1"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_twilio(session, phone, meta):
    keys = load_keys().get("twilio")
    if not keys or not keys.get("account_sid") or not keys.get("auth_token"):
        return {"configured": False, "note": "No Twilio credentials configured"}
    url = f"{SUPPORTED_APIS['twilio']['url']}{phone}?Type=carrier&Type=caller-name"
    r = safe_request(session, url, auth=(keys["account_sid"], keys["auth_token"]), timeout=18)
    if not r:
        return None
    return r.json()

def source_truecaller(session, phone, meta):
    keys = load_keys().get("truecaller")
    if not keys or not keys.get("authorization"):
        return {"configured": False, "note": "No Truecaller authorization configured"}
    url = f"{SUPPORTED_APIS['truecaller']['url']}?q={phone}&countryCode={meta.get('region','')}&type=4&placement=SEARCHRESULTS,HISTORY,DETAILS&encoding=json"
    headers = {"Authorization": f"Bearer {keys['authorization']}", "Accept": "application/json"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_google_dork(session, phone, meta):
    queries = [
        f'"{phone}"',
        f'"{phone}" "contact"',
        f'"{phone}" "téléphone"',
        f'"{phone}" intext:nom',
        f'"{phone}" filetype:pdf',
        f'"{phone}" site:linkedin.com',
        f'"{phone}" site:facebook.com',
        f'"{phone}" site:twitter.com',
        f'"{phone}" "prenom"',
        f'"{phone}" "adresse"',
    ]
    return {"dorks": queries, "note": "Use these queries manually or with a SERP API"}

def source_local_bridges(session, phone, meta):
    variants = [
        phone,
        phone.lstrip("+"),
        phone.replace(" ", ""),
        phone.replace("-", ""),
        phone.replace(".", ""),
        f"0{phone[-9:]}" if len(phone) >= 9 else phone,
    ]
    return {"variants": list(set(variants))}

def source_github(session, phone, meta):
    if not HAS_REQUESTS:
        return None
    url = f"https://api.github.com/search/code?q=%22{phone}%22&per_page=5"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    data = r.json()
    items = []
    for item in data.get("items", [])[:5]:
        items.append({
            "repo": item.get("repository", {}).get("full_name"),
            "path": item.get("path"),
            "url": item.get("html_url"),
        })
    return {"matches": items}

def source_pastebin(session, phone, meta):
    return {"note": "Pastebin scraping requires scraping API or Pro subscription", "query": f"https://www.google.com/search?q=site:pastebin.com+%22{phone}%22"}

def source_haveibeenpwned(session, phone, meta):
    return {"note": "HIBP does not support phone lookups directly", "query": f"https://haveibeenpwned.com"}

def source_carrier_info(session, phone, meta):
    return {
        "carrier": meta.get("carrier"),
        "country": meta.get("country"),
        "region": meta.get("region"),
        "timezones": meta.get("timezones"),
        "valid": meta.get("valid"),
    }

def source_social_hint(session, phone, meta):
    return {
        "whatsapp": f"https://wa.me/{phone.lstrip('+')}",
        "telegram": f"https://t.me/+{phone.lstrip('+')}",
        "signal": "Check Signal manually",
        "viber": "Check Viber manually",
    }

def source_reverse_lookup_fr(session, phone, meta):
    local = phone
    if local.startswith("33") and len(local) > 9:
        local = "0" + local[2:]
    return {
        "pagesjaunes_query": f"https://www.pagesjaunes.fr/annuaireinverse/recherche?quoiqui={local}",
        "118712_query": f"https://www.118712.fr/recherche/inverse/{local}",
        "annuaire_inverse": f"https://www.annuaire-inverse.com/recherche/{local}",
    }

def source_national_format(session, phone, meta):
    if not HAS_PHONENUMBERS:
        return None
    try:
        x = phonenumbers.parse(phone, None)
    except Exception:
        try:
            x = phonenumbers.parse(phone, "FR")
        except Exception:
            return None
    return {
        "international": phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "national": phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.NATIONAL),
        "e164": phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.E164),
        "rfc3966": phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.RFC3966),
    }

def source_open_cnam(session, phone, meta):
    keys = load_keys().get("opencnam")
    if not keys or not keys.get("account_sid") or not keys.get("auth_token"):
        return {"configured": False, "note": "No OpenCNAM credentials configured"}
    url = f"https://api.opencnam.com/v3/phone/{phone}?account_sid={keys['account_sid']}&auth_token={keys['auth_token']}&format=json"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_telnyx(session, phone, meta):
    keys = load_keys().get("telnyx")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Telnyx API key configured"}
    url = f"https://api.telnyx.com/v2/number_lookup/{phone}"
    headers = {"Authorization": f"Bearer {keys['api_key']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_seon(session, phone, meta):
    keys = load_keys().get("seon")
    if not keys or not keys.get("license_key"):
        return {"configured": False, "note": "No SEON license key configured"}
    url = "https://api.seon.io/SeonRestService/phone-api/v1/{phone}"
    headers = {"X-API-KEY": keys["license_key"], "Content-Type": "application/json"}
    r = safe_request(session, url.format(phone=phone), headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_ipqs(session, phone, meta):
    keys = load_keys().get("ipqs")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No IPQualityScore key configured"}
    url = f"https://ipqualityscore.com/api/json/phone/{keys['api_key']}/{phone}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_numlookupapi(session, phone, meta):
    keys = load_keys().get("numlookupapi")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No NumLookupAPI key configured"}
    url = f"https://api.numlookupapi.com/v1/validate/{phone}?apikey={keys['api_key']}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_callhippo(session, phone, meta):
    return {"note": "CallHippo requires account access", "query": f"https://callhippo.com"}

def source_belong(session, phone, meta):
    return {"note": "Belong data requires partner API access", "query": f"https://belong.com"}

def source_ekata(session, phone, meta):
    keys = load_keys().get("ekata")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Ekata API key configured"}
    url = f"https://api.ekata.com/3.0/phone?api_key={keys['api_key']}&phone={phone}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_neutrino(session, phone, meta):
    keys = load_keys().get("neutrino")
    if not keys or not keys.get("user_id") or not keys.get("api_key"):
        return {"configured": False, "note": "No Neutrino API credentials configured"}
    url = "https://neutrinoapi.net/phone-verify"
    data = {"user-id": keys["user_id"], "api-key": keys["api_key"], "number": phone}
    r = safe_request(session, url, method="POST", data=data, timeout=18)
    if not r:
        return None
    return r.json()

def source_whitepages(session, phone, meta):
    return {"note": "Whitepages Pro requires partner API key", "query": f"https://pro.whitepages.com"}

def source_anywho(session, phone, meta):
    return {"note": "AnyWho reverse lookup is US-only", "query": f"https://www.anywho.com/phone/{phone}"}

def source_spokeo(session, phone, meta):
    return {"note": "Spokeo requires subscription or scraping", "query": f"https://www.spokeo.com/search?c=1&q={phone}"}

def source_zabasearch(session, phone, meta):
    return {"note": "ZabaSearch reverse phone is US-only", "query": f"https://www.zabasearch.com/phone/{phone}"}

def source_beenverified(session, phone, meta):
    return {"note": "BeenVerified requires subscription", "query": f"https://www.beenverified.com/app/rc/phone/{phone}"}

def source_intelius(session, phone, meta):
    return {"note": "Intelius requires subscription", "query": f"https://www.intelius.com/phone/{phone}"}

def source_usphonebook(session, phone, meta):
    return {"note": "USPhoneBook reverse lookup", "query": f"https://www.usphonebook.com/{phone}"}

def source_peoplefinders(session, phone, meta):
    return {"note": "PeopleFinders requires subscription", "query": f"https://www.peoplefinders.com/phone/{phone}"}

def source_coco_finder(session, phone, meta):
    return {"note": "CocoFinder reverse phone", "query": f"https://cocofinder.com/phone-search"}

def source_truthfinder(session, phone, meta):
    return {"note": "TruthFinder requires subscription", "query": f"https://www.truthfinder.com/phone-search"}

def source_instant_checkmate(session, phone, meta):
    return {"note": "Instant CheckMate requires subscription", "query": f"https://www.instantcheckmate.com/phone"}

def source_spy_dialer(session, phone, meta):
    return {"note": "SpyDialer free reverse lookup", "query": f"https://www.spydialer.com"}

def source_truepeoplesearch(session, phone, meta):
    return {"note": "TruePeopleSearch reverse phone", "query": f"https://www.truepeoplesearch.com/results?phoneno={phone}"}

def source_fastpeoplesearch(session, phone, meta):
    return {"note": "FastPeopleSearch reverse phone", "query": f"https://www.fastpeoplesearch.com/{phone}"}

def source_thatsthem(session, phone, meta):
    return {"note": "ThatsThem reverse phone", "query": f"https://thatsthem.com/phone/{phone}"}

def source_okcaller(session, phone, meta):
    return {"note": "OKCaller reverse lookup", "query": f"https://www.okcaller.com/detail.php?number={phone}"}

def source_numlook(session, phone, meta):
    return {"note": "NumLook free reverse lookup", "query": f"https://www.numlook.com/{phone}"}

def source_free_carrier_lookup(session, phone, meta):
    return {"note": "FreeCarrierLookup free carrier lookup", "query": f"https://www.freecarrierlookup.com"}

def source_data24(session, phone, meta):
    return {"note": "Data24-7 SMS lookup requires API", "query": f"https://www.data24-7.com"}

def source_trestle(session, phone, meta):
    return {"note": "Trestle identity data requires API key", "query": f"https://trestleiq.com"}

def source_twilio_addon_cnam(session, phone, meta):
    keys = load_keys().get("twilio")
    if not keys or not keys.get("account_sid") or not keys.get("auth_token"):
        return {"configured": False, "note": "No Twilio credentials configured"}
    url = f"https://lookups.twilio.com/v1/PhoneNumbers/{phone}?AddOns=twilio_caller_name_lookup"
    r = safe_request(session, url, auth=(keys["account_sid"], keys["auth_token"]), timeout=18)
    if not r:
        return None
    return r.json()

def source_vonage(session, phone, meta):
    keys = load_keys().get("vonage")
    if not keys or not keys.get("api_key") or not keys.get("api_secret"):
        return {"configured": False, "note": "No Vonage credentials configured"}
    url = f"https://api.nexmo.com/v1/ni/basic/net?api_key={keys['api_key']}&api_secret={keys['api_secret']}&number={phone}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_sinoh(session, phone, meta):
    return {"note": "SINOH data requires partner access", "query": f"https://sinoh.io"}

def source_numberingplans(session, phone, meta):
    return {"note": "NumberingPlans requires subscription", "query": f"https://www.numberingplans.com"}

def source_localcallingguide(session, phone, meta):
    return {"note": "LocalCallingGuide rate center lookup", "query": f"https://www.localcallingguide.com/lca/"}

def source_fonefinder(session, phone, meta):
    return {"note": "Fone Finder exchange lookup", "query": f"http://www.fonefinder.net"}

def source_worldphonebook(session, phone, meta):
    return {"note": "World Phonebook lookup", "query": f"https://worldphonebook.com"}

def source_numinfo(session, phone, meta):
    return {"note": "NumInfo lookup", "query": f"https://numinfo.io/{phone}"}

def source_callerroute(session, phone, meta):
    return {"note": "CallerRoute lookup", "query": f"https://callerroute.com/number/{phone}"}

def source_tellows(session, phone, meta):
    return {"note": "Tellows spam score", "query": f"https://www.tellows.fr/num/{phone}"}

def source_shouldianswer(session, phone, meta):
    return {"note": "Should I Answer spam score", "query": f"https://www.shouldianswer.com/phone-number/{phone}"}

def source_scamcallfighters(session, phone, meta):
    return {"note": "Scam Call Fighters reports", "query": f"https://www.scamcallfighters.com/search-phone-{phone}.html"}

def source_800notes(session, phone, meta):
    return {"note": "800Notes reports", "query": f"https://800notes.com/Phone.aspx/{phone}"}

def source_mrnumber(session, phone, meta):
    return {"note": "Mr. Number reports", "query": f"https://mrnumber.com/{phone}"}

def source_callfilter(session, phone, meta):
    return {"note": "CallFilter reports", "query": f"https://callfilter.app/{phone}"}

def source_hiya(session, phone, meta):
    return {"note": "Hiya spam lookup", "query": f"https://www.hiya.com/{phone}"}

def source_nomlaki(session, phone, meta):
    return {"note": "Nomorobo lookup", "query": f"https://www.nomorobo.com/lookup/{phone}"}

def source_callprotect(session, phone, meta):
    return {"note": "AT&T Call Protect", "query": f"https://www.att.com/support/article/call-protect"}

def source_youmail(session, phone, meta):
    return {"note": "YouMail directory", "query": f"https://www.youmail.com/lookup"}

def source_sync_me(session, phone, meta):
    return {"note": "Sync.ME caller ID", "query": f"https://sync.me"}

def source_callapp(session, phone, meta):
    return {"note": "CallApp caller ID", "query": f"https://callapp.com"}

def source_showcaller(session, phone, meta):
    return {"note": "Showcaller ID", "query": f"https://www.showcaller.net"}

def source_callhero(session, phone, meta):
    return {"note": "CallHero spam lookup", "query": f"https://callhero.com"}

def source_unknownphone(session, phone, meta):
    return {"note": "UnknownPhone reports", "query": f"https://unknownphone.com/phone/{phone}"}

def source_whotextedme(session, phone, meta):
    return {"note": "WhoTextedMe lookup", "query": f"https://whotextedme.com/{phone}"}

def source_phoneowner(session, phone, meta):
    return {"note": "PhoneOwner lookup", "query": f"https://phoneowner.com/{phone}"}

def source_calleridtest(session, phone, meta):
    return {"note": "CallerIDTest lookup", "query": f"https://calleridtest.com/{phone}"}

def source_cnam_info(session, phone, meta):
    return {"note": "Free CNAM lookup services", "query": f"https://cnam.info"}

def source_opencnam_free(session, phone, meta):
    return {"note": "OpenCNAM free tier", "query": f"https://www.opencnam.com"}

def source_twilio_free_lookup(session, phone, meta):
    return {"note": "Twilio free format lookup", "query": f"https://www.twilio.com/lookup"}

def source_phoneregistry(session, phone, meta):
    return {"note": "PhoneRegistry lookup", "query": f"https://www.phoneregistry.com"}

def source_reversegenie(session, phone, meta):
    return {"note": "ReverseGenie lookup", "query": f"https://www.reversegenie.com/phone/{phone}"}

def source_cellrevealer(session, phone, meta):
    return {"note": "CellRevealer lookup", "query": f"https://www.cellrevealer.com"}

def source_phonehistory(session, phone, meta):
    return {"note": "PhoneHistory lookup", "query": f"https://phonehistory.com/{phone}"}

def source_usphonevalidation(session, phone, meta):
    return {"note": "US Phone Validation", "query": f"https://www.phonevalidator.com/index.aspx"}

def source_numverify_alternative(session, phone, meta):
    return {"note": "Alternative Numverify-style validation", "query": f"https://numverify.com"}

def source_abstractapi(session, phone, meta):
    keys = load_keys().get("abstractapi")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No AbstractAPI key configured"}
    url = f"https://phonevalidation.abstractapi.com/v1/?api_key={keys['api_key']}&phone={phone}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_veriphone(session, phone, meta):
    keys = load_keys().get("veriphone")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Veriphone key configured"}
    url = f"https://api.veriphone.io/v2/verify?phone={phone}&key={keys['api_key']}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_loqate(session, phone, meta):
    keys = load_keys().get("loqate")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Loqate key configured"}
    url = f"https://api.addressy.com/PhoneNumberValidation/Interactive/Validate/v2.20/json3.ws?Key={keys['api_key']}&Phone={phone}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_numvalidate(session, phone, meta):
    return {"note": "NumValidate free validation", "query": f"https://numvalidate.com/api/{phone}"}

def source_phone_number_ai(session, phone, meta):
    return {"note": "PhoneNumber.AI lookup", "query": f"https://phoneumber.ai"}

def source_clearoutphone(session, phone, meta):
    keys = load_keys().get("clearout")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Clearout key configured"}
    url = f"https://api.clearout.io/phone/{phone}"
    headers = {"Authorization": keys["api_key"]}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_messente(session, phone, meta):
    keys = load_keys().get("messente")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Messente key configured"}
    url = f"https://api.messente.com/v1/phonebook/{phone}"
    headers = {"Authorization": f"Bearer {keys['api_key']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_telesign(session, phone, meta):
    keys = load_keys().get("telesign")
    if not keys or not keys.get("customer_id") or not keys.get("api_key"):
        return {"configured": False, "note": "No Telesign credentials configured"}
    url = f"https://rest-api.telesign.com/v1/phoneid/{phone}"
    headers = {"Authorization": f"Basic {keys['customer_id']}:{keys['api_key']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_sms_api(session, phone, meta):
    keys = load_keys().get("smsapi")
    if not keys or not keys.get("token"):
        return {"configured": False, "note": "No SMSAPI token configured"}
    url = f"https://api.smsapi.com/phonebook/contacts?phone={phone}"
    headers = {"Authorization": f"Bearer {keys['token']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_ringover(session, phone, meta):
    return {"note": "Ringover cloud phone", "query": f"https://www.ringover.com"}

def source_aircall(session, phone, meta):
    return {"note": "Aircall cloud phone", "query": f"https://aircall.io"}

def source_justcall(session, phone, meta):
    return {"note": "JustCall cloud phone", "query": f"https://justcall.io"}

def source_cloudtalk(session, phone, meta):
    return {"note": "CloudTalk phone system", "query": f"https://www.cloudtalk.io"}

def source_ozonetel(session, phone, meta):
    return {"note": "Ozonetel cloud contact center", "query": f"https://www.ozonetel.com"}

def source_exotel(session, phone, meta):
    return {"note": "Exotel cloud telephony", "query": f"https://exotel.com"}

def source_knowlarity(session, phone, meta):
    return {"note": "Knowlarity cloud telephony", "query": f"https://www.knowlarity.com"}

def source_myoperator(session, phone, meta):
    return {"note": "MyOperator cloud phone", "query": f"https://myoperator.com"}

def source_callhippo_api(session, phone, meta):
    keys = load_keys().get("callhippo")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No CallHippo API key configured"}
    url = f"https://api.callhippo.com/api/v3/numbers/{phone}"
    headers = {"Authorization": f"Bearer {keys['api_key']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_freshcaller(session, phone, meta):
    return {"note": "Freshcaller cloud PBX", "query": f"https://freshcaller.com"}

def source_avoxi(session, phone, meta):
    return {"note": "AVOXI virtual numbers", "query": f"https://www.avoxi.com"}

def source_tollfreeforwarding(session, phone, meta):
    return {"note": "TollFreeForwarding numbers", "query": f"https://www.tollfreeforwarding.com"}

def source_voxbone(session, phone, meta):
    return {"note": "Voxbone (Bandwidth) numbers", "query": f"https://www.voxbone.com"}

def source_plivo(session, phone, meta):
    keys = load_keys().get("plivo")
    if not keys or not keys.get("auth_id") or not keys.get("auth_token"):
        return {"configured": False, "note": "No Plivo credentials configured"}
    url = f"https://api.plivo.com/v1/Account/{keys['auth_id']}/Number/{phone}/"
    r = safe_request(session, url, auth=(keys["auth_id"], keys["auth_token"]), timeout=18)
    if not r:
        return None
    return r.json()

def source_bandwidth(session, phone, meta):
    keys = load_keys().get("bandwidth")
    if not keys or not keys.get("account_id") or not keys.get("api_username") or not keys.get("api_password"):
        return {"configured": False, "note": "No Bandwidth credentials configured"}
    url = f"https://dashboard.bandwidth.com/api/accounts/{keys['account_id']}/tn/{phone}"
    r = safe_request(session, url, auth=(keys["api_username"], keys["api_password"]), timeout=18)
    if not r:
        return None
    return r.text

def source_flowroute(session, phone, meta):
    keys = load_keys().get("flowroute")
    if not keys or not keys.get("access_key") or not keys.get("secret_key"):
        return {"configured": False, "note": "No Flowroute credentials configured"}
    url = f"https://api.flowroute.com/v2.2/numbers/{phone}"
    r = safe_request(session, url, auth=(keys["access_key"], keys["secret_key"]), timeout=18)
    if not r:
        return None
    return r.json()

def source_teli(session, phone, meta):
    return {"note": "Teli communications", "query": f"https://teli.net"}

def source_voximplant(session, phone, meta):
    return {"note": "Voximplant platform", "query": f"https://voximplant.com"}

def source_sipgate(session, phone, meta):
    return {"note": "Sipgate telephony", "query": f"https://www.sipgate.de"}

def source_messagebird(session, phone, meta):
    keys = load_keys().get("messagebird")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No MessageBird key configured"}
    url = f"https://rest.messagebird.com/lookup/{phone}"
    headers = {"Authorization": f"AccessKey {keys['api_key']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_sinch(session, phone, meta):
    keys = load_keys().get("sinch")
    if not keys or not keys.get("access_key") or not keys.get("access_secret"):
        return {"configured": False, "note": "No Sinch credentials configured"}
    url = f"https://callingapi.sinch.com/v1/calling/query/number/{phone}"
    headers = {"Authorization": f"Basic {keys['access_key']}:{keys['access_secret']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_infobip(session, phone, meta):
    keys = load_keys().get("infobip")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Infobip key configured"}
    url = f"https://api.infobip.com/number/1/numbers/{phone}"
    headers = {"Authorization": f"App {keys['api_key']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_clickatell(session, phone, meta):
    keys = load_keys().get("clickatell")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Clickatell key configured"}
    url = f"https://platform.clickatell.com/public-client/number/{phone}"
    headers = {"Authorization": keys["api_key"]}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_nexmo_number_insight(session, phone, meta):
    keys = load_keys().get("vonage")
    if not keys or not keys.get("api_key") or not keys.get("api_secret"):
        return {"configured": False, "note": "No Vonage credentials configured"}
    url = f"https://api.nexmo.com/ni/advanced/json?api_key={keys['api_key']}&api_secret={keys['api_secret']}&number={phone}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_d7networks(session, phone, meta):
    keys = load_keys().get("d7networks")
    if not keys or not keys.get("api_token"):
        return {"configured": False, "note": "No D7Networks token configured"}
    url = f"https://api.d7networks.com/verify/v1/lookup/{phone}"
    headers = {"Authorization": f"Token {keys['api_token']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_route_mobile(session, phone, meta):
    return {"note": "Route Mobile lookup", "query": f"https://routemobile.com"}

def source_tyntec(session, phone, meta):
    keys = load_keys().get("tyntec")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No tyntec key configured"}
    url = f"https://api.tyntec.com/numbering/v1/number/{phone}"
    headers = {"Authorization": f"Bearer {keys['api_key']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_hubspot_caller_id(session, phone, meta):
    return {"note": "HubSpot caller ID", "query": f"https://www.hubspot.com"}

def source_zoho_caller_id(session, phone, meta):
    return {"note": "Zoho CRM caller ID", "query": f"https://www.zoho.com"}

def source_salesforce(session, phone, meta):
    return {"note": "Salesforce contact lookup", "query": f"https://salesforce.com"}

def source_pipedrive(session, phone, meta):
    return {"note": "Pipedrive contact lookup", "query": f"https://www.pipedrive.com"}

def source_nimble(session, phone, meta):
    return {"note": "Nimble CRM lookup", "query": f"https://www.nimble.com"}

def source_nutshell(session, phone, meta):
    return {"note": "Nutshell CRM lookup", "query": f"https://www.nutshell.com"}

def source_insightly(session, phone, meta):
    return {"note": "Insightly CRM lookup", "query": f"https://www.insightly.com"}

def source_copper(session, phone, meta):
    return {"note": "Copper CRM lookup", "query": f"https://www.copper.com"}

def source_capsule(session, phone, meta):
    return {"note": "Capsule CRM lookup", "query": f"https://capsulecrm.com"}

def source_less_annoying_crm(session, phone, meta):
    return {"note": "Less Annoying CRM lookup", "query": f"https://www.lessannoyingcrm.com"}

def source_apollo(session, phone, meta):
    return {"note": "Apollo.io contact lookup", "query": f"https://www.apollo.io"}

def source_lusha(session, phone, meta):
    return {"note": "Lusha contact enrichment", "query": f"https://www.lusha.com"}

def source_hunter(session, phone, meta):
    return {"note": "Hunter.io email/phone finder", "query": f"https://hunter.io"}

def source_kaspr(session, phone, meta):
    return {"note": "Kaspr contact data", "query": f"https://www.kaspr.io"}

def source_snov(session, phone, meta):
    return {"note": "Snov.io email/phone finder", "query": f"https://snov.io"}

def source_rocketreach(session, phone, meta):
    return {"note": "RocketReach contact finder", "query": f"https://rocketreach.co"}

def source_uplead(session, phone, meta):
    return {"note": "UpLead contact finder", "query": f"https://www.uplead.com"}

def source_contactout(session, phone, meta):
    return {"note": "ContactOut contact finder", "query": f"https://contactout.com"}

def source_getprospect(session, phone, meta):
    return {"note": "GetProspect contact finder", "query": f"https://getprospect.com"}

def source_anymailfinder(session, phone, meta):
    return {"note": "Anymailfinder email finder", "query": f"https://anymailfinder.com"}

def source_voilanorbert(session, phone, meta):
    return {"note": "VoilaNorbert email finder", "query": f"https://www.voilanorbert.com"}

def source_findymail(session, phone, meta):
    return {"note": "Findymail email finder", "query": f"https://findymail.com"}

def source_skymem(session, phone, meta):
    return {"note": "SkyMem email/phone search", "query": f"https://www.skymem.info"}

def source_emailrep(session, phone, meta):
    return {"note": "EmailRep reputation", "query": f"https://emailrep.io"}

def source_pipl(session, phone, meta):
    keys = load_keys().get("pipl")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Pipl API key configured"}
    url = f"https://api.pipl.com/search/v5/?phone={phone}&key={keys['api_key']}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_fullcontact(session, phone, meta):
    keys = load_keys().get("fullcontact")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No FullContact key configured"}
    url = "https://api.fullcontact.com/v3/person.enrich"
    headers = {"Authorization": f"Bearer {keys['api_key']}", "Content-Type": "application/json"}
    r = safe_request(session, url, method="POST", headers=headers, data=json.dumps({"phone": phone}), timeout=18)
    if not r:
        return None
    return r.json()

def source_spokeo_api(session, phone, meta):
    keys = load_keys().get("spokeo")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Spokeo API key configured"}
    url = f"https://api.spokeo.com/v1/phone/{phone}?api_key={keys['api_key']}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_beenverified_api(session, phone, meta):
    return {"note": "BeenVerified API requires partnership", "query": f"https://www.beenverified.com"}

def source_truthfinder_api(session, phone, meta):
    return {"note": "TruthFinder API requires partnership", "query": f"https://www.truthfinder.com"}

def source_peoplelooker(session, phone, meta):
    return {"note": "PeopleLooker lookup", "query": f"https://www.peoplelooker.com"}

def source_checkpeople(session, phone, meta):
    return {"note": "CheckPeople lookup", "query": f"https://www.checkpeople.com"}

def source_peekyou(session, phone, meta):
    return {"note": "PeekYou people search", "query": f"https://www.peekyou.com"}

def source_radaris(session, phone, meta):
    return {"note": "Radaris people search", "query": f"https://radaris.com"}

def source_ussearch(session, phone, meta):
    return {"note": "US Search people search", "query": f"https://www.ussearch.com"}

def source_peoplesearchnow(session, phone, meta):
    return {"note": "PeopleSearchNow lookup", "query": f"https://www.peoplesearchnow.com"}

def source_advanced_background_checks(session, phone, meta):
    return {"note": "Advanced Background Checks", "query": f"https://www.advancedbackgroundchecks.com"}

def source_checkthemsession(phone, meta):
    return {"note": "CheckThem lookup", "query": f"https://checkthem.com"}

def source_golookup(session, phone, meta):
    return {"note": "GoLookup lookup", "query": f"https://golookup.com"}

def source_instant_chechemas(session, phone, meta):
    return {"note": "Instant Checkmate API", "query": f"https://www.instantcheckmate.com"}

def source_idtrue(session, phone, meta):
    return {"note": "IDTrue background check", "query": f"https://www.idtrue.com"}

def source_goodhire(session, phone, meta):
    return {"note": "GoodHire background check", "query": f"https://www.goodhire.com"}

def source_checkr(session, phone, meta):
    return {"note": "Checkr background check API", "query": f"https://checkr.com"}

def source_sterling(session, phone, meta):
    return {"note": "Sterling background check", "query": f"https://www.sterlingcheck.com"}

def source_hireright(session, phone, meta):
    return {"note": "HireRight background check", "query": f"https://www.hireright.com"}

def source_first_advantage(session, phone, meta):
    return {"note": "First Advantage screening", "query": f"https://www.fadv.com"}

def source_veriff(session, phone, meta):
    return {"note": "Veriff identity verification", "query": f"https://www.veriff.com"}

def source_onfido(session, phone, meta):
    return {"note": "Onfido identity verification", "query": f"https://onfido.com"}

def source_jumio(session, phone, meta):
    return {"note": "Jumio identity verification", "query": f"https://www.jumio.com"}

def source_trulioo(session, phone, meta):
    return {"note": "Trulioo identity verification", "query": f"https://www.trulioo.com"}

def source_sheerid(session, phone, meta):
    return {"note": "SheerID verification", "query": f"https://www.sheerid.com"}

def source_persona(session, phone, meta):
    return {"note": "Persona identity verification", "query": f"https://withpersona.com"}

def source_socure(session, phone, meta):
    return {"note": "Socure identity verification", "query": f"https://www.socure.com"}

def source_sentilink(session, phone, meta):
    return {"note": "SentiLink fraud prevention", "query": f"https://www.sentilink.com"}

def source_idology(session, phone, meta):
    return {"note": "IDology identity verification", "query": f"https://www.idology.com"}

def source_lexisnexis(session, phone, meta):
    return {"note": "LexisNexis Risk Solutions", "query": f"https://risk.lexisnexis.com"}

def source_thomson_reuters(session, phone, meta):
    return {"note": "Thomson Reuters CLEAR", "query": f"https://www.thomsonreuters.com"}

def source_transunion(session, phone, meta):
    return {"note": "TransUnion TLOxp", "query": f"https://www.transunion.com"}

def source_experian(session, phone, meta):
    return {"note": "Experian identity services", "query": f"https://www.experian.com"}

def source_equifax(session, phone, meta):
    return {"note": "Equifax identity services", "query": f"https://www.equifax.com"}

def source_acxiom(session, phone, meta):
    return {"note": "Acxiom data services", "query": f"https://www.acxiom.com"}

def source_live_ramp(session, phone, meta):
    return {"note": "LiveRamp identity resolution", "query": f"https://liveramp.com"}

def source_neustar(session, phone, meta):
    return {"note": "Neustar identity data", "query": f"https://www.home.neustar"}

def source_facebook_graph(session, phone, meta):
    return {"note": "Facebook Graph API phone search requires app permissions", "query": f"https://developers.facebook.com"}

def source_twitter_api(session, phone, meta):
    keys = load_keys().get("twitter")
    if not keys or not keys.get("bearer_token"):
        return {"configured": False, "note": "No Twitter/X bearer token configured"}
    url = f"https://api.twitter.com/2/tweets/search/recent?query={phone}&max_results=10"
    headers = {"Authorization": f"Bearer {keys['bearer_token']}"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_linkedin(session, phone, meta):
    return {"note": "LinkedIn phone search requires authenticated access", "query": f"https://www.linkedin.com"}

def source_instagram(session, phone, meta):
    return {"note": "Instagram phone search requires authenticated access", "query": f"https://www.instagram.com"}

def source_tiktok(session, phone, meta):
    return {"note": "TikTok phone search requires authenticated access", "query": f"https://www.tiktok.com"}

def source_reddit(session, phone, meta):
    if not HAS_REQUESTS:
        return None
    url = f"https://www.reddit.com/search.json?q={phone}&limit=10"
    headers = {"User-Agent": "HI-Resolver/1.0"}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    data = r.json()
    posts = []
    for child in data.get("data", {}).get("children", [])[:5]:
        p = child.get("data", {})
        posts.append({"title": p.get("title"), "subreddit": p.get("subreddit"), "url": f"https://reddit.com{p.get('permalink','')}"})
    return {"posts": posts}

def source_vk(session, phone, meta):
    keys = load_keys().get("vk")
    if not keys or not keys.get("access_token"):
        return {"configured": False, "note": "No VK access token configured"}
    url = f"https://api.vk.com/method/users.search?q={phone}&access_token={keys['access_token']}&v=5.199"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_odnoklassniki(session, phone, meta):
    return {"note": "Odnoklassniki search requires API access", "query": f"https://ok.ru"}

def source_discord(session, phone, meta):
    return {"note": "Discord does not expose phone search", "query": f"https://discord.com"}

def source_telegram_api(session, phone, meta):
    return {"note": "Telegram API requires MTProto authorization", "query": f"https://core.telegram.org"}

def source_signal_api(session, phone, meta):
    return {"note": "Signal does not provide public phone lookup", "query": f"https://signal.org"}

def source_whatsapp_api(session, phone, meta):
    return {"note": "WhatsApp Business API requires Meta approval", "query": f"https://business.whatsapp.com/products/business-platform"}

def source_viber_api(session, phone, meta):
    return {"note": "Viber API requires official bot account", "query": f"https://developers.viber.com"}

def source_line_api(session, phone, meta):
    return {"note": "LINE API requires official channel", "query": f"https://developers.line.biz"}

def source_wechat(session, phone, meta):
    return {"note": "WeChat does not expose phone search", "query": f"https://www.wechat.com"}

def source_qq(session, phone, meta):
    return {"note": "QQ does not expose phone search", "query": f"https://im.qq.com"}

def source_snapchat(session, phone, meta):
    return {"note": "Snapchat does not expose phone search", "query": f"https://www.snapchat.com"}

def source_pinterest(session, phone, meta):
    return {"note": "Pinterest phone search requires API", "query": f"https://www.pinterest.com"}

def source_tumblr(session, phone, meta):
    if not HAS_REQUESTS:
        return None
    url = f"https://www.tumblr.com/search/{phone}"
    return {"note": "Tumblr public search", "query": url}

def source_medium(session, phone, meta):
    if not HAS_REQUESTS:
        return None
    url = f"https://medium.com/search?q={phone}"
    return {"note": "Medium public search", "query": url}

def source_quora(session, phone, meta):
    return {"note": "Quora search", "query": f"https://www.quora.com/search?q={phone}"}

def source_youtube(session, phone, meta):
    return {"note": "YouTube search", "query": f"https://www.youtube.com/results?search_query={phone}"}

def source_twitch(session, phone, meta):
    return {"note": "Twitch user search", "query": f"https://www.twitch.tv/search?term={phone}"}

def source_github_gist(session, phone, meta):
    if not HAS_REQUESTS:
        return None
    url = f"https://api.github.com/gists/public?per_page=100"
    return {"note": "GitHub gists public feed (search via GitHub Code Search recommended)", "query": url}

def source_gitlab(session, phone, meta):
    return {"note": "GitLab search", "query": f"https://gitlab.com/search?search={phone}"}

def source_bitbucket(session, phone, meta):
    return {"note": "Bitbucket search", "query": f"https://bitbucket.org/search?q={phone}"}

def source_stackoverflow(session, phone, meta):
    if not HAS_REQUESTS:
        return None
    url = f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=activity&intitle={phone}&site=stackoverflow"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    data = r.json()
    items = []
    for item in data.get("items", [])[:5]:
        items.append({"title": item.get("title"), "link": item.get("link"), "owner": item.get("owner", {}).get("display_name")})
    return {"items": items}

def source_pastebin_search(session, phone, meta):
    return {"note": "PasteBin scraping via Google", "query": f"https://www.google.com/search?q=site:pastebin.com+%22{phone}%22"}

def source_shodan(session, phone, meta):
    keys = load_keys().get("shodan")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No Shodan key configured"}
    url = f"https://api.shodan.io/shodan/host/search?key={keys['api_key']}&query={phone}"
    r = safe_request(session, url, timeout=18)
    if not r:
        return None
    return r.json()

def source_censys(session, phone, meta):
    keys = load_keys().get("censys")
    if not keys or not keys.get("api_id") or not keys.get("api_secret"):
        return {"configured": False, "note": "No Censys credentials configured"}
    url = f"https://search.censys.io/api/v2/hosts/search?q={phone}"
    r = safe_request(session, url, auth=(keys["api_id"], keys["api_secret"]), timeout=18)
    if not r:
        return None
    return r.json()

def source_virustotal(session, phone, meta):
    keys = load_keys().get("virustotal")
    if not keys or not keys.get("api_key"):
        return {"configured": False, "note": "No VirusTotal key configured"}
    url = f"https://www.virustotal.com/api/v3/search?query={phone}"
    headers = {"x-apikey": keys["api_key"]}
    r = safe_request(session, url, headers=headers, timeout=18)
    if not r:
        return None
    return r.json()

def source_urlscan(session, phone, meta):
    return {"note": "URLscan search", "query": f"https://urlscan.io/search/#{phone}"}

def source_publicwww(session, phone, meta):
    return {"note": "PublicWWW source code search", "query": f"https://publicwww.com/websites/{phone}/"}

def source_wikileaks(session, phone, meta):
    return {"note": "WikiLeaks search", "query": f"https://search.wikileaks.org/?query={phone}"}

def source_osint_framework(session, phone, meta):
    return {"note": "OSINT Framework phone resources", "query": f"https://osintframework.com"}

def source_osint_curious(session, phone, meta):
    return {"note": "OSINT Curious phone resources", "query": f"https://osintcurious.net"}

def source_bellingcat(session, phone, meta):
    return {"note": "Bellingcat resources", "query": f"https://www.bellingcat.com"}

def source_trace_labs(session, phone, meta):
    return {"note": "Trace Labs OSINT resources", "query": f"https://www.tracelabs.org"}

def source_my_osint_training(session, phone, meta):
    return {"note": "My OSINT Training resources", "query": f"https://www.myosinttraining.com"}

def source_inteltechniques(session, phone, meta):
    return {"note": "IntelTechniques phone search tools", "query": f"https://inteltechniques.com/tools/Phone.html"}

def source_osintcombine(session, phone, meta):
    return {"note": "OSINT Combine resources", "query": f"https://www.osintcombine.com"}

def source_sans_osint(session, phone, meta):
    return {"note": "SANS OSINT resources", "query": f"https://www.sans.org/osint/"}

def source_henry_baker(session, phone, meta):
    return {"note": "Phone OSINT checklist", "query": f"https://github.com/PhoneOSINT"}

def source_osint_dojo(session, phone, meta):
    return {"note": "OSINT Dojo resources", "query": f"https://www.osintdojo.com"}

SOURCES = [
    PhoneSource("metadata", source_carrier_info),
    PhoneSource("national_format", source_national_format),
    PhoneSource("local_bridges", source_local_bridges),
    PhoneSource("reverse_fr", source_reverse_lookup_fr),
    PhoneSource("social_hint", source_social_hint),
    PhoneSource("google_dork", source_google_dork),
    PhoneSource("github", source_github),
    PhoneSource("reddit", source_reddit),
    PhoneSource("stackoverflow", source_stackoverflow),
    PhoneSource("twitter_api", source_twitter_api),
    PhoneSource("vk", source_vk),
    PhoneSource("tumblr", source_tumblr),
    PhoneSource("medium", source_medium),
    PhoneSource("youtube", source_youtube),
    PhoneSource("quora", source_quora),
    PhoneSource("pastebin", source_pastebin),
    PhoneSource("shodan", source_shodan),
    PhoneSource("censys", source_censys),
    PhoneSource("virustotal", source_virustotal),
    PhoneSource("urlscan", source_urlscan),
    PhoneSource("publicwww", source_publicwww),
    PhoneSource("wikileaks", source_wikileaks),
    PhoneSource("numverify", source_numverify),
    PhoneSource("twilio", source_twilio),
    PhoneSource("truecaller", source_truecaller),
    PhoneSource("opencnam", source_open_cnam),
    PhoneSource("telnyx", source_telnyx),
    PhoneSource("seon", source_seon),
    PhoneSource("ipqs", source_ipqs),
    PhoneSource("numlookupapi", source_numlookupapi),
    PhoneSource("ekata", source_ekata),
    PhoneSource("neutrino", source_neutrino),
    PhoneSource("abstractapi", source_abstractapi),
    PhoneSource("veriphone", source_veriphone),
    PhoneSource("loqate", source_loqate),
    PhoneSource("clearout", source_clearoutphone),
    PhoneSource("messente", source_messente),
    PhoneSource("telesign", source_telesign),
    PhoneSource("messagebird", source_messagebird),
    PhoneSource("sinch", source_sinch),
    PhoneSource("infobip", source_infobip),
    PhoneSource("clickatell", source_clickatell),
    PhoneSource("vonage", source_vonage),
    PhoneSource("nexmo", source_nexmo_number_insight),
    PhoneSource("d7networks", source_d7networks),
    PhoneSource("tyntec", source_tyntec),
    PhoneSource("plivo", source_plivo),
    PhoneSource("bandwidth", source_bandwidth),
    PhoneSource("flowroute", source_flowroute),
    PhoneSource("pipl", source_pipl),
    PhoneSource("fullcontact", source_fullcontact),
    PhoneSource("spokeo_api", source_spokeo_api),
    PhoneSource("tellows", source_tellows),
    PhoneSource("shouldianswer", source_shouldianswer),
    PhoneSource("scamcallfighters", source_scamcallfighters),
    PhoneSource("800notes", source_800notes),
    PhoneSource("mrnumber", source_mrnumber),
    PhoneSource("callfilter", source_callfilter),
    PhoneSource("hiya", source_hiya),
    PhoneSource("nomorobo", source_callprotect),
    PhoneSource("youmail", source_youmail),
    PhoneSource("syncme", source_sync_me),
    PhoneSource("callapp", source_callapp),
    PhoneSource("showcaller", source_showcaller),
    PhoneSource("callhero", source_callhero),
    PhoneSource("unknownphone", source_unknownphone),
    PhoneSource("whotextedme", source_whotextedme),
    PhoneSource("phoneowner", source_phoneowner),
    PhoneSource("calleridtest", source_calleridtest),
    PhoneSource("cnam", source_cnam_info),
    PhoneSource("pagesjaunes", source_reverse_lookup_fr),
    PhoneSource("118712", source_reverse_lookup_fr),
    PhoneSource("anywho", source_anywho),
    PhoneSource("spokeo", source_spokeo),
    PhoneSource("zabasearch", source_zabasearch),
    PhoneSource("beenverified", source_beenverified),
    PhoneSource("intelius", source_intelius),
    PhoneSource("usphonebook", source_usphonebook),
    PhoneSource("peoplefinders", source_peoplefinders),
    PhoneSource("truthfinder", source_truthfinder),
    PhoneSource("instantcheckmate", source_instant_checkmate),
    PhoneSource("spydialer", source_spy_dialer),
    PhoneSource("truepeoplesearch", source_truepeoplesearch),
    PhoneSource("fastpeoplesearch", source_fastpeoplesearch),
    PhoneSource("thatsthem", source_thatsthem),
    PhoneSource("okcaller", source_okcaller),
    PhoneSource("numlook", source_numlook),
    PhoneSource("freecarrierlookup", source_free_carrier_lookup),
    PhoneSource("data24", source_data24),
    PhoneSource("trestle", source_trestle),
    PhoneSource("whitepages", source_whitepages),
    PhoneSource("linkedin", source_linkedin),
    PhoneSource("instagram", source_instagram),
    PhoneSource("tiktok", source_tiktok),
    PhoneSource("facebook", source_facebook_graph),
    PhoneSource("telegram", source_telegram_api),
    PhoneSource("whatsapp", source_whatsapp_api),
    PhoneSource("signal", source_signal_api),
    PhoneSource("viber", source_viber_api),
    PhoneSource("line", source_line_api),
    PhoneSource("wechat", source_wechat),
    PhoneSource("qq", source_qq),
    PhoneSource("snapchat", source_snapchat),
    PhoneSource("pinterest", source_pinterest),
    PhoneSource("twitch", source_twitch),
    PhoneSource("gitlab", source_gitlab),
    PhoneSource("bitbucket", source_bitbucket),
    PhoneSource("github_gist", source_github_gist),
    PhoneSource("hubspot", source_hubspot_caller_id),
    PhoneSource("zoho", source_zoho_caller_id),
    PhoneSource("salesforce", source_salesforce),
    PhoneSource("pipedrive", source_pipedrive),
    PhoneSource("nimble", source_nimble),
    PhoneSource("nutshell", source_nutshell),
    PhoneSource("insightly", source_insightly),
    PhoneSource("copper", source_copper),
    PhoneSource("capsule", source_capsule),
    PhoneSource("lessannoyingcrm", source_less_annoying_crm),
    PhoneSource("apollo", source_apollo),
    PhoneSource("lusha", source_lusha),
    PhoneSource("hunter", source_hunter),
    PhoneSource("kaspr", source_kaspr),
    PhoneSource("snov", source_snov),
    PhoneSource("rocketreach", source_rocketreach),
    PhoneSource("uplead", source_uplead),
    PhoneSource("contactout", source_contactout),
    PhoneSource("getprospect", source_getprospect),
    PhoneSource("anymailfinder", source_anymailfinder),
    PhoneSource("voilanorbert", source_voilanorbert),
    PhoneSource("findymail", source_findymail),
    PhoneSource("skymem", source_skymem),
    PhoneSource("emailrep", source_emailrep),
    PhoneSource("peoplelooker", source_peoplelooker),
    PhoneSource("checkpeople", source_checkpeople),
    PhoneSource("peekyou", source_peekyou),
    PhoneSource("radaris", source_radaris),
    PhoneSource("ussearch", source_ussearch),
    PhoneSource("peoplesearchnow", source_peoplesearchnow),
    PhoneSource("advancedbackgroundchecks", source_advanced_background_checks),
    PhoneSource("checkthem", source_checkthemsession),
    PhoneSource("golookup", source_golookup),
    PhoneSource("idtrue", source_idtrue),
    PhoneSource("goodhire", source_goodhire),
    PhoneSource("checkr", source_checkr),
    PhoneSource("sterling", source_sterling),
    PhoneSource("hireright", source_hireright),
    PhoneSource("firstadvantage", source_first_advantage),
    PhoneSource("veriff", source_veriff),
    PhoneSource("onfido", source_onfido),
    PhoneSource("jumio", source_jumio),
    PhoneSource("trulioo", source_trulioo),
    PhoneSource("sheerid", source_sheerid),
    PhoneSource("persona", source_persona),
    PhoneSource("socure", source_socure),
    PhoneSource("sentilink", source_sentilink),
    PhoneSource("idology", source_idology),
    PhoneSource("lexisnexis", source_lexisnexis),
    PhoneSource("thomsonreuters", source_thomson_reuters),
    PhoneSource("transunion", source_transunion),
    PhoneSource("experian", source_experian),
    PhoneSource("equifax", source_equifax),
    PhoneSource("acxiom", source_acxiom),
    PhoneSource("liveramp", source_live_ramp),
    PhoneSource("neustar", source_neustar),
    PhoneSource("osint_framework", source_osint_framework),
    PhoneSource("osintcurious", source_osint_curious),
    PhoneSource("bellingcat", source_bellingcat),
    PhoneSource("tracelabs", source_trace_labs),
    PhoneSource("myosinttraining", source_my_osint_training),
    PhoneSource("inteltechniques", source_inteltechniques),
    PhoneSource("osintcombine", source_osintcombine),
    PhoneSource("sansosint", source_sans_osint),
    PhoneSource("osintdojo", source_osint_dojo),
]

# ────────────────────────────────
# IDENTITY EXTRACTION
# ────────────────────────────────
NAME_PATTERNS = [
    re.compile(r"[A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+", re.UNICODE),
    re.compile(r"[A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+", re.UNICODE),
    re.compile(r"M\.\s+[A-Z][a-zà-ÿ]+", re.UNICODE),
    re.compile(r"Mme\.?\s+[A-Z][a-zà-ÿ]+", re.UNICODE),
    re.compile(r"Dr\.?\s+[A-Z][a-zà-ÿ]+", re.UNICODE),
]

def extract_names(text):
    names = set()
    if not isinstance(text, str):
        return []
    for pat in NAME_PATTERNS:
        for m in pat.finditer(text):
            names.add(m.group(0))
    return sorted(names)

def extract_emails(text):
    if not isinstance(text, str):
        return []
    return sorted(set(re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)))

def extract_addresses(text):
    if not isinstance(text, str):
        return []
    return sorted(set(re.findall(r"\d+\s+[\w\s]+(?:rue|avenue|boulevard|route|chemin|impasse|place|allée|bd|av|r)\b[\w\s]*", text, re.IGNORECASE)))

# ────────────────────────────────
# RESULT AGGREGATION
# ────────────────────────────────
def run_lookup(phone, args):
    meta = get_phone_metadata(phone)
    if not meta.get("valid") and not args.force:
        print(f"{C.YELLOW}[!] Number appears invalid. Use --force to scan anyway.{C.RESET}")
    session = http_session()
    enabled = set(args.sources.split(",")) if args.sources else set(s.name for s in SOURCES)
    selected = [s for s in SOURCES if s.name in enabled]
    if args.exclude:
        excluded = set(args.exclude.split(","))
        selected = [s for s in selected if s.name not in excluded]
    results = []
    pb = ProgressBar(len(selected), prefix="Scanning", suffix="Done")
    if args.threads > 1:
        with ThreadPoolExecutor(max_workers=args.threads) as ex:
            futures = {ex.submit(s.run, session, phone, meta): s for s in selected}
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)
                pb.update(1, message=res.get("source", ""))
    else:
        for s in selected:
            res = s.run(session, phone, meta)
            results.append(res)
            pb.update(1, message=res.get("source", ""))
    pb.finish("Scan complete")
    return {"phone": phone, "meta": meta, "results": results, "timestamp": datetime.now().isoformat()}

def infer_identity(report):
    candidates = []
    text_blob = json.dumps(report, ensure_ascii=False)
    names = extract_names(text_blob)
    emails = extract_emails(text_blob)
    addresses = extract_addresses(text_blob)
    for res in report.get("results", []):
        data = res.get("data") or {}
        if isinstance(data, dict):
            for key in ["caller_name", "name", "full_name", "first_name", "last_name", "owner", "carrier", "operator"]:
                val = data.get(key)
                if val:
                    candidates.append({"field": key, "value": val, "source": res.get("source")})
    return {"names": names[:20], "emails": emails[:20], "addresses": addresses[:20], "fields": candidates[:20]}

def print_report(report, args):
    print()
    print_centered("IDENTITY INTELLIGENCE REPORT", width=70)
    print(f"{C.CYAN}Target:{C.RESET}    {C.BOLD}{report['phone']}{C.RESET}")
    if report['meta'].get('valid'):
        print(f"{C.GREEN}Valid:{C.RESET}     Yes ({report['meta'].get('country')})")
    else:
        print(f"{C.YELLOW}Valid:{C.RESET}     No / unknown")
    print(f"{C.CYAN}Region:{C.RESET}    {report['meta'].get('region','-')}")
    print(f"{C.CYAN}Carrier:{C.RESET}   {report['meta'].get('carrier','-')}")
    print(f"{C.CYAN}Type:{C.RESET}      {report['meta'].get('type','-')}")
    print()
    identity = infer_identity(report)
    if identity["names"]:
        print(f"{C.GREEN}{C.BOLD}Possible names:{C.RESET}")
        for n in identity["names"][:10]:
            print(f"  • {n}")
    if identity["emails"]:
        print(f"{C.GREEN}{C.BOLD}Possible emails:{C.RESET}")
        for e in identity["emails"][:10]:
            print(f"  • {e}")
    if identity["addresses"]:
        print(f"{C.GREEN}{C.BOLD}Possible addresses:{C.RESET}")
        for a in identity["addresses"][:10]:
            print(f"  • {a}")
    print()
    if args.verbose:
        print(f"{C.BRIGHT_GREEN}{C.BOLD}Raw source results:{C.RESET}")
        for res in report["results"]:
            src = res.get("source")
            cached = " [cached]" if res.get("cached") else ""
            err = res.get("error")
            data = res.get("data")
            print(f"{C.CYAN}─ {src}{cached}{C.RESET}")
            if err:
                print(f"  {C.RED}error: {err}{C.RESET}")
            elif data:
                for line in json.dumps(data, indent=2, ensure_ascii=False).splitlines()[:20]:
                    print(f"  {line}")
    print_centered("END OF REPORT", width=70)

def save_report(report, args):
    if not args.export:
        return
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(EXPORT_DIR, f"hi_{report['phone']}_{timestamp}")
    if args.export in ("json", "all"):
        save_json(f"{base}.json", report)
        print(f"{C.GREEN}[+] Saved JSON: {base}.json{C.RESET}")
    if args.export in ("txt", "all"):
        with open(f"{base}.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"{C.GREEN}[+] Saved TXT: {base}.txt{C.RESET}")
    if args.export in ("csv", "all"):
        with open(f"{base}.csv", "w", encoding="utf-8") as f:
            f.write("source,value\n")
            identity = infer_identity(report)
            for n in identity.get("names", []):
                f.write(f"name,{n}\n")
            for e in identity.get("emails", []):
                f.write(f"email,{e}\n")
            for a in identity.get("addresses", []):
                f.write(f"address,{a}\n")
        print(f"{C.GREEN}[+] Saved CSV: {base}.csv{C.RESET}")

def save_history(report):
    ensure_dirs()
    history = load_json(HISTORY_FILE, [])
    history.append({"phone": report["phone"], "timestamp": report["timestamp"]})
    save_json(HISTORY_FILE, history[-500:])

# ────────────────────────────────
# CLI
# ────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(
        prog="HI",
        description="HI — Phone Intelligence & Identity Resolver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python HI.py +33612345678
          python HI.py 0612345678 --threads 8 --export json
          python HI.py +14155552671 --sources numverify,twilio,truecaller
          python HI.py --configure numverify
        """),
    )
    p.add_argument("phone", nargs="?", help="Phone number to investigate")
    p.add_argument("--version", action="version", version=f"HI {__version__}")
    p.add_argument("--configure", metavar="API", help="Configure API key for a supported API")
    p.add_argument("--list-sources", action="store_true", help="List all available sources")
    p.add_argument("--sources", metavar="LIST", help="Comma-separated list of sources to run")
    p.add_argument("--exclude", metavar="LIST", help="Comma-separated list of sources to exclude")
    p.add_argument("--threads", type=int, default=DEFAULT_THREADS, help=f"Number of threads (default {DEFAULT_THREADS})")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Request timeout (default {DEFAULT_TIMEOUT})")
    p.add_argument("--export", choices=["json", "txt", "csv", "all"], help="Export report")
    p.add_argument("--no-cache", action="store_true", help="Disable cache")
    p.add_argument("--no-log", action="store_true", help="Disable logging")
    p.add_argument("--verbose", "-v", action="store_true", help="Show raw source output")
    p.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    p.add_argument("--force", action="store_true", help="Force scan even if number looks invalid")
    return p

def list_sources():
    print(f"{C.BRIGHT_GREEN}{C.BOLD}Available sources ({len(SOURCES)}):{C.RESET}")
    for s in SOURCES:
        print(f"  {C.CYAN}{s.name}{C.RESET}")

def main():
    global ENABLE_CACHE, ENABLE_LOG, QUIET_MODE, VERBOSE_MODE, DEFAULT_TIMEOUT
    ensure_dirs()
    parser = build_parser()
    args = parser.parse_args()
    if args.no_cache:
        ENABLE_CACHE = False
    if args.no_log:
        ENABLE_LOG = False
    QUIET_MODE = args.quiet
    VERBOSE_MODE = args.verbose
    DEFAULT_TIMEOUT = args.timeout
    if not QUIET_MODE:
        print_banner()
    if args.configure:
        if args.configure not in SUPPORTED_APIS:
            print(f"{C.RED}[!] Unknown API: {args.configure}{C.RESET}")
            print(f"{C.YELLOW}Supported: {', '.join(SUPPORTED_APIS.keys())}{C.RESET}")
            sys.exit(1)
        prompt_key(args.configure)
        sys.exit(0)
    if args.list_sources:
        list_sources()
        sys.exit(0)
    if not args.phone:
        parser.print_help()
        sys.exit(1)
    phone = normalize_phone(args.phone)
    if not phone:
        print(f"{C.RED}[!] Invalid phone number.{C.RESET}")
        sys.exit(1)
    intl = format_international(args.phone)
    if intl:
        phone = re.sub(r"\D", "", intl)
    log_event(f"Lookup started for {phone}")
    report = run_lookup(phone, args)
    save_history(report)
    print_report(report, args)
    save_report(report, args)
    log_event(f"Lookup completed for {phone}")

if __name__ == "__main__":
    main()
