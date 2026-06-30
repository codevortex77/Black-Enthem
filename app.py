from flask import Flask, request, jsonify
import requests
import time
from datetime import datetime

app = Flask(__name__)

# 1. FIX FOR CREDIT AT THE END: 
# Prevent Flask from sorting JSON keys alphabetically so "Credit" stays at the bottom
app.config['JSON_SORT_KEYS'] = False
if hasattr(app, 'json'):
    app.json.sort_keys = False

# Simple cache
cache = {}
CACHE_DURATION = 300  # 5 minutes

# 2. API VALIDITY (18 Days from June 30, 2026)
EXPIRY_DATE = datetime(2026, 7, 18)

def get_cached_response(cache_key):
    if cache_key in cache:
        data, timestamp = cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cache(cache_key, data):
    cache[cache_key] = (data, time.time())

def clean_response(data, top_level=True):
    if isinstance(data, dict):
        cleaned = {}

        for key, value in data.items():
            if key in ['req_left', 'req_total', 'expiry', 'developer']:
                continue

            if isinstance(value, str):
                cleaned[key] = value.replace('@simpleguy444', '@RichUniversal')
            else:
                cleaned[key] = clean_response(value, False)

        # Add Credit only to the root object. Since sorting is disabled, 
        # inserting it last guarantees it shows up at the bottom of the JSON.
        if top_level:
            cleaned["Credit"] = "@RichUniversal"

        return cleaned

    elif isinstance(data, list):
        return [clean_response(item, False) for item in data]

    elif isinstance(data, str):
        return data.replace('@simpleguy444', '@RichUniversal')

    return data

@app.route('/api', methods=['GET'])
def api_handler():
    # --- Validity Check ---
    if datetime.now() > EXPIRY_DATE:
        return jsonify({
            "error": "API has expired. Validity was for 18 days.", 
            "Credit": "@RichUniversal"
        }), 403

    # --- 3. KEY ENFORCEMENT ---
    provided_key = request.args.get('key', '')
    if provided_key.lower() != 'blackenthem':
        return jsonify({
            "error": "Access Denied. Invalid API key.", 
            "Credit": "@RichUniversal"
        }), 401

    # Extract parameters (supporting both 'query' and 'term' based on your example URL)
    query_type = request.args.get('type', 'num') 
    query_value = request.args.get('query') or request.args.get('term', '')
    
    if not query_value:
        return jsonify({"error": "Query or term parameter required", "Credit": "@RichUniversal"}), 400
    
    # Create cache key
    cache_key = f"{query_type}:blackenthem:{query_value}"
    
    # Check cache
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return jsonify(cached_response)
    
    try:
        # Request to original API
        # We pass 'swayam' to the backend to keep it working, while users use 'Blackenthem' on the frontend
        backend_key = "swayam"
        original_url = f"https://rootx-osint.in/?type={query_type}&key={backend_key}&query={query_value}"
        
        response = requests.get(original_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Clean the response
            cleaned_data = clean_response(data)
            
            # Cache it
            set_cache(cache_key, cleaned_data)
            
            return jsonify(cleaned_data)
        else:
            return jsonify({"error": "Failed to fetch data from upstream", "Credit": "@RichUniversal"}), 500
            
    except Exception as e:
        return jsonify({
            "error": str(e),
            "Credit": "@RichUniversal"
        }), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "System Online",
        "valid_until": EXPIRY_DATE.strftime('%Y-%m-%d'),
        "Credit": "@RichUniversal",
        "usage": "/api?key=Blackenthem&type=mobile&term=9758126124"
    })

# Vercel handler
def handler(request, context):
    return app(request.environ, start_response)
