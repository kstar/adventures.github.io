import json
import os
import hashlib
import hmac
import datetime
import uuid
import boto3
from boto3.dynamodb.conditions import Key

# Configuration
ALLOWED_ORIGIN = "https://adventuresindeepspace.com"
DEVELOPMENT_ORIGIN = "http://localhost:4000" # for local testing if needed
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "ads_analytics")
SECRET_KEY = os.environ.get("ANALYTICS_SECRET", "default_secret_please_change")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def get_header(headers, name):
    # Case-insensitive helper to retrieve headers
    name_lower = name.lower()
    for k, v in headers.items():
        if k.lower() == name_lower:
            return v
    return ""

def get_cors_headers(origin):
    allowed = [ALLOWED_ORIGIN, DEVELOPMENT_ORIGIN]
    origin_to_return = ALLOWED_ORIGIN
    
    if origin in allowed:
        origin_to_return = origin
        
    return {
        "Access-Control-Allow-Origin": origin_to_return,
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin"
    }

def get_visitor_hash(ip, user_agent, secret, date_str):
    daily_salt = hmac.new(secret.encode(), date_str.encode(), hashlib.sha256).hexdigest()
    # Visitor Hash = SHA256(IP + UserAgent + Daily Salt)
    raw_str = f"{ip}|{user_agent}|{daily_salt}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def classify_referrer(referrer):
    if not referrer:
        return "Direct"
    ref_lower = referrer.lower()
    
    # Search engines
    if any(x in ref_lower for x in ["google.com", "bing.com", "yahoo.com", "duckduckgo.com", "baidu.com", "yandex"]):
        return "Search Engine"
    # AI Tools
    if any(x in ref_lower for x in ["chatgpt.com", "openai.com", "claude.ai", "anthropic.com", "gemini.google.com", "perplexity.ai"]):
        return "AI Tool"
    # Social Media
    if any(x in ref_lower for x in ["facebook.com", "t.co", "twitter.com", "x.com", "reddit.com", "instagram.com", "linkedin.com"]):
        return "Social Media"
        
    try:
        domain = referrer.split("//")[1].split("/")[0]
        return domain
    except Exception:
        return "Other"

def classify_visitor_type(user_agent):
    ua_lower = user_agent.lower()
    
    # 1. AI Agents
    ai_agents = [
        "gptbot", "chatgpt-user", "claudebot", "claude-web", "anthropic",
        "google-extended", "perplexitybot", "imagesiftbot", "cohere-ai",
        "omgilibot", "facebookexternalhit", "bytespider", "diffbot"
    ]
    if any(bot in ua_lower for bot in ai_agents):
        return "AI Bot"
        
    # 2. Search Engine Crawlers
    search_crawlers = [
        "googlebot", "bingbot", "yandexbot", "baiduspider", "duckduckbot",
        "slurp", "sogou", "ia_archiver"
    ]
    if any(crawler in ua_lower for crawler in search_crawlers):
        return "Search Bot"
        
    # 3. Generic Crawlers / Scrapers / Headless Browsers
    generic_bots = [
        "headless", "selenium", "playwright", "puppeteer", "phantomjs",
        "scrapy", "curl", "wget", "python-requests", "http-client",
        "bot", "spider", "crawler", "scrape"
    ]
    if any(bot in ua_lower for bot in generic_bots):
        return "Generic Bot"
        
    return "Human"

def handle_options(event):
    origin = get_header(event.get("headers", {}), "origin")
    return {
        "statusCode": 204,
        "headers": get_cors_headers(origin),
        "body": ""
    }

def handle_post(event):
    headers = event.get("headers", {})
    origin = get_header(headers, "origin")
    
    # Strict Origin / Referer check
    allowed_origins = [ALLOWED_ORIGIN, DEVELOPMENT_ORIGIN]
    if origin not in allowed_origins:
        referer = get_header(headers, "referer")
        if not any(x in referer for x in allowed_origins):
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Forbidden Origin"})
            }

    try:
        body = json.loads(event.get("body", "{}"))
    except Exception:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON"})
        }

    event_type = body.get("event", "pageview")
    path = body.get("path", "/")
    raw_referrer = body.get("referrer", "")
    details = body.get("details", "")
    
    # Get request IP
    ip = event.get("requestContext", {}).get("http", {}).get("sourceIp", "0.0.0.0")
    user_agent = get_header(headers, "user-agent") or "unknown"
    
    # Country detection from CloudFront headers passed to Function URL
    country_code = get_header(headers, "cloudfront-viewer-country") or "Unknown"
    
    # Classify Visitor Type (Human, AI Bot, Search Bot, Generic Bot)
    visitor_type = classify_visitor_type(user_agent)
    
    # Unique ID and date
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.isoformat() + "Z"
    unique_id = str(uuid.uuid4())
    
    # hash calculation
    visitor_hash = get_visitor_hash(ip, user_agent, SECRET_KEY, date_str)
    
    # Save to DynamoDB
    if event_type == "pageview":
        referrer_type = classify_referrer(raw_referrer)
        table.put_item(
            Item={
                "PK": f"PAGEVIEW#{date_str}",
                "SK": f"TIME#{timestamp_str}#{unique_id}",
                "path": path,
                "referrer": raw_referrer or "Direct",
                "referrer_type": referrer_type,
                "country": country_code,
                "visitor_hash": visitor_hash,
                "visitor_type": visitor_type,
                "timestamp": timestamp_str
            }
        )
    else:
        table.put_item(
            Item={
                "PK": f"EVENT#{date_str}#{event_type}",
                "SK": f"TIME#{timestamp_str}#{unique_id}",
                "path": path,
                "details": details,
                "visitor_hash": visitor_hash,
                "visitor_type": visitor_type,
                "timestamp": timestamp_str
            }
        )
        
    return {
        "statusCode": 200,
        "headers": get_cors_headers(origin),
        "body": json.dumps({"status": "success"})
    }

def handle_get_dashboard(event):
    # Query last 7 days of data for the dashboard
    today = datetime.date.today()
    dates = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    pageviews = []
    events_data = []
    
    for d in dates:
        try:
            # Query Pageviews
            resp = table.query(
                KeyConditionExpression=Key("PK").eq(f"PAGEVIEW#{d}")
            )
            pageviews.extend(resp.get("Items", []))
            
            # Query CSV Export Events
            resp_csv = table.query(
                KeyConditionExpression=Key("PK").eq(f"EVENT#{d}#csv_export")
            )
            events_data.extend(resp_csv.get("Items", []))
            
            # Query Anchor Clicks
            resp_anchor = table.query(
                KeyConditionExpression=Key("PK").eq(f"EVENT#{d}#anchor_click")
            )
            events_data.extend(resp_anchor.get("Items", []))
        except Exception as e:
            print(f"Error querying date {d}: {e}")
            
    # Process aggregates (Human Only vs All Traffic)
    human_views = [pv for pv in pageviews if pv.get("visitor_type", "Human") == "Human"]
    total_human_views = len(human_views)
    unique_human_visitors = len(set(x["visitor_hash"] for x in human_views))
    
    total_raw_views = len(pageviews)
    unique_raw_visitors = len(set(x["visitor_hash"] for x in pageviews))
    
    # Visitor type breakdown counts
    visitor_types = {"Human": 0, "AI Bot": 0, "Search Bot": 0, "Generic Bot": 0}
    for pv in pageviews:
        vt = pv.get("visitor_type", "Human")
        visitor_types[vt] = visitor_types.get(vt, 0) + 1
        
    # Referrer breakdown (Human Only)
    referrers = {}
    for pv in human_views:
        ref_type = pv.get("referrer_type", "Direct")
        referrers[ref_type] = referrers.get(ref_type, 0) + 1
        
    # Country breakdown (Human Only)
    countries = {}
    for pv in human_views:
        c = pv.get("country", "Unknown")
        countries[c] = countries.get(c, 0) + 1
        
    # Top Pages breakdown (Human Only)
    pages = {}
    for pv in human_views:
        p = pv.get("path", "/")
        pages[p] = pages.get(p, 0) + 1
        
    # CSV Exports (Human Only)
    csv_count = sum(1 for e in events_data if "csv_export" in e.get("PK", "") and e.get("visitor_type", "Human") == "Human")
    
    # Top clicked anchors (Human Only)
    anchors = {}
    for e in events_data:
        if "anchor_click" in e.get("PK", "") and e.get("visitor_type", "Human") == "Human":
            anc = e.get("details", "unknown")
            anchors[anc] = anchors.get(anc, 0) + 1

    summary = {
        "total_human_views": total_human_views,
        "unique_human_visitors": unique_human_visitors,
        "total_raw_views": total_raw_views,
        "unique_raw_visitors": unique_raw_visitors,
        "visitor_types": visitor_types,
        "referrers": referrers,
        "countries": countries,
        "pages": pages,
        "csv_exports": csv_count,
        "anchors": anchors
    }
    
    # Return HTML Dashboard
    html_content = get_dashboard_html(summary)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        },
        "body": html_content
    }

def get_dashboard_html(data):
    # Generate bot list details for table
    bot_rows = "".join(f"<tr><td><span class='badge bot-badge'>{bot_type}</span></td><td><strong>{count}</strong></td></tr>" 
                      for bot_type, count in data["visitor_types"].items() if bot_type != "Human")

    # Render a premium, beautiful dashboard with glassmorphism and modern colors
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Adventures in Deep Space - Analytics</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --primary: #3b82f6;
            --accent: #10b981;
            --warning: #f59e0b;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
        }}
        h1 {{
            font-weight: 700;
            font-size: 2rem;
            margin: 0 0 5px 0;
            background: linear-gradient(to right, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 0.95rem;
            margin: 0;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 40px rgba(59, 130, 246, 0.1);
        }}
        .card-title {{
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .card-value {{
            font-size: 2.2rem;
            font-weight: 700;
            color: #ffffff;
        }}
        .grid-tables {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .table-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            overflow-x: auto;
        }}
        .table-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 0.9rem;
        }}
        th {{
            color: var(--text-muted);
            font-weight: 600;
        }}
        td {{
            color: var(--text-main);
        }}
        .badge {{
            background: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .bot-badge {{
            background: rgba(245, 158, 11, 0.15);
            color: #fcd34d;
        }}
        .indicator {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent);
            margin-right: 8px;
        }}
        .info-pill {{
            background: rgba(255, 255, 255, 0.05);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Analytics Dashboard</h1>
                <p class="subtitle">Adventures in Deep Space • Serverless (Last 7 Days)</p>
            </div>
            <div class="info-pill">
                <span class="indicator"></span>
                <span>Active Tracking</span>
            </div>
        </header>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">Unique Human Visitors</div>
                <div class="card-value">{data["unique_human_visitors"]}</div>
            </div>
            <div class="card">
                <div class="card-title">Human Pageviews</div>
                <div class="card-value">{data["total_human_views"]}</div>
            </div>
            <div class="card">
                <div class="card-title">CSV Exports (Humans)</div>
                <div class="card-value">{data["csv_exports"]}</div>
            </div>
            <div class="card">
                <div class="card-title">Total Bot Traffic</div>
                <div class="card-value">{data["total_raw_views"] - data["total_human_views"]}</div>
            </div>
        </div>

        <div class="grid-tables">
            <div class="table-card">
                <div class="table-title">Top Visited Pages (Human Only)</div>
                <table>
                    <thead>
                        <tr><th>Path</th><th>Views</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td><code>{path}</code></td><td><strong>{count}</strong></td></tr>" for path, count in sorted(data["pages"].items(), key=lambda x: x[1], reverse=True)[:10]) or "<tr><td colspan='2' style='color:var(--text-muted); text-align:center;'>No human pageviews yet</td></tr>"}
                    </tbody>
                </table>
            </div>

            <div class="table-card">
                <div class="table-title">Referrer Channels (Human Only)</div>
                <table>
                    <thead>
                        <tr><th>Source</th><th>Views</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td><span class='badge'>{ref}</span></td><td><strong>{count}</strong></td></tr>" for ref, count in sorted(data["referrers"].items(), key=lambda x: x[1], reverse=True)) or "<tr><td colspan='2' style='color:var(--text-muted); text-align:center;'>No referrers recorded</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="grid-tables">
            <div class="table-card">
                <div class="table-title">Geography (Countries - Human Only)</div>
                <table>
                    <thead>
                        <tr><th>Country</th><th>Visits</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td>🌍 {country}</td><td><strong>{count}</strong></td></tr>" for country, count in sorted(data["countries"].items(), key=lambda x: x[1], reverse=True)) or "<tr><td colspan='2' style='color:var(--text-muted); text-align:center;'>No geographics recorded</td></tr>"}
                    </tbody>
                </table>
            </div>

            <div class="table-card">
                <div class="table-title">Top Constellations / Anchors Clicked</div>
                <table>
                    <thead>
                        <tr><th>Anchor Name</th><th>Clicks</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td><code>#{anchor}</code></td><td><strong>{count}</strong></td></tr>" for anchor, count in sorted(data["anchors"].items(), key=lambda x: x[1], reverse=True)[:10]) or "<tr><td colspan='2' style='color:var(--text-muted); text-align:center;'>No anchors clicked yet</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="grid-tables" style="margin-top: 20px;">
            <div class="table-card" style="grid-column: span 2;">
                <div class="table-title">Crawler & Scraping Bot Breakdown</div>
                <table>
                    <thead>
                        <tr><th>Bot Type</th><th>Requests Intercepted</th></tr>
                    </thead>
                    <tbody>
                        {bot_rows}
                        <tr style="border-top: 1px solid var(--border-color);">
                            <td><strong>Total Bot Requests</strong></td>
                            <td><strong>{data["total_raw_views"] - data["total_human_views"]}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    
    if method == "OPTIONS":
        return handle_options(event)
    elif method == "POST":
        return handle_post(event)
    elif method == "GET":
        return handle_get_dashboard(event)
        
    return {
        "statusCode": 405,
        "body": json.dumps({"error": "Method Not Allowed"})
    }
