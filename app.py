"""
J.A.R.V.I.S. // GEMINI CORE EDITION - Main Server (app.py)
Combines the Salvaged HP 605747-001 Open-Frame HUD Spec with full Gemini-like capabilities:
- Multi-turn conversational AI (Gemini 2.5 Flash default + Claude + Groq)
- PDF, Code, and Document Upload & Analysis (/api/upload)
- Live Web & Encyclopedia Knowledge Search (Wikipedia + DuckDuckGo)
- Open-Meteo Live Weather Telemetry (/api/weather)
- Direct System Clock & Hardware Telemetry (/api/system)
- Offline pyttsx3 Text-to-Speech Voice Synthesis
"""
import os
import re
import time
import platform
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import psutil
from modules.weather_service import get_weather
from modules.tts_service import voice_engine
from modules.llm_service import (
    query_llm,
    save_api_config,
    get_key_status,
    set_uploaded_document,
    clear_memory,
)
from modules.web_search import search_web_knowledge
from modules.document_reader import extract_file_content

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB upload limit
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BOOT_TIME = time.time()
WEB_SEARCH_HINTS = (
    "current",
    "currently",
    "latest",
    "recent",
    "today",
    "tonight",
    "this week",
    "this month",
    "news",
    "breaking",
    "price",
    "stock",
    "exchange rate",
    "score",
    "schedule",
    "release date",
    "search for",
    "search the web",
    "search online",
    "look up",
    "look up online",
)
WEATHER_REQUEST_PATTERN = re.compile(
    r"\b(weather|forecast|is it raining|will it rain|rain today|"
    r"temperature (?:in|at|for)|humidity (?:in|at|for)|"
    r"wind speed|wind (?:in|at|for))\b",
    re.IGNORECASE,
)


@app.route("/")
def index():
    """Render the Iron Man J.A.R.V.I.S. // Gemini Core Holographic HUD."""
    return render_template("index.html")


@app.route("/api/system", methods=["GET"])
def api_system():
    """Read time from system clock and report CPU/RAM status + AI key status."""
    now = datetime.now()
    uptime_sec = int(time.time() - BOOT_TIME)
    hours, rem = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(rem, 60)

    mem = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=None)
    key_info = get_key_status()

    return jsonify({
        "time_24h": now.strftime("%H:%M:%S"),
        "time_12h": now.strftime("%I:%M:%S %p"),
        "date_formatted": now.strftime("%A, %d %B %Y").upper(),
        "timezone": time.tzname[0] if time.tzname else "LOCAL",
        "uptime": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
        "cpu_percent": round(cpu_pct, 1),
        "ram_percent": round(mem.percent, 1),
        "ram_used_gb": round(mem.used / (1024 ** 3), 2),
        "ram_total_gb": round(mem.total / (1024 ** 3), 2),
        "hardware_id": "HP-605747-001 // GEMINI CORE HUD",
        "os_platform": f"{platform.system()} {platform.release()}",
        "key_status": key_info,
    })


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    """Get or update AI Provider & API Key directly from the HUD UI."""
    if request.method == "GET":
        return jsonify(get_key_status())

    payload = request.get_json(force=True) or {}
    provider = payload.get("provider", "gemini")
    api_key = payload.get("api_key", "")
    model_name = payload.get("model_name", "")
    status = save_api_config(provider, api_key, model_name)
    return jsonify({"status": "SAVED", "key_status": status})


@app.route("/api/clear", methods=["POST"])
def api_clear():
    """Clear conversation memory and active document context."""
    clear_memory()
    return jsonify({"status": "CLEARED"})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """
    Upload a PDF, code file (.py, .c, .js, .html), Markdown, or CSV file
    so J.A.R.V.I.S. can read it and build/answer from it just like Gemini.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file attached."}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename."}), 400

    safe_name = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_FOLDER, safe_path := safe_name)
    f.save(save_path)

    extracted = extract_file_content(save_path, safe_name)
    set_uploaded_document(safe_name, extracted)

    preview = extracted[:350].replace("\n", " ") + ("..." if len(extracted) > 350 else "")
    return jsonify({
        "status": "LOADED",
        "filename": safe_name,
        "chars": len(extracted),
        "preview": preview,
    })


@app.route("/api/weather", methods=["GET"])
def api_weather():
    """Fetch live weather from Open-Meteo API (free, no key required)."""
    city = request.args.get("city", os.getenv("DEFAULT_CITY", "Panaji")).strip()
    lat = float(os.getenv("DEFAULT_LAT", "15.4909"))
    lon = float(os.getenv("DEFAULT_LON", "73.8278"))
    data = get_weather(city=city, lat=lat, lon=lon)
    return jsonify(data)


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """
    Unified J.A.R.V.I.S. // Gemini Autonomous Router:
    1. Checks system clock / hardware status requests.
    2. Checks live weather requests (Open-Meteo).
    3. Queries live Web Knowledge (Wikipedia / DuckDuckGo) for factual grounding.
    4. Sends full multi-turn context + active uploaded PDF/code file to Gemini (or Claude/Groq).
    """
    payload = request.get_json(force=True) or {}
    query = (payload.get("query") or "").strip()
    speak = bool(payload.get("speak", True))

    if not query:
        return jsonify({"error": "Empty command received."}), 400

    q_low = query.lower()
    context_notes = []
    weather_result = None

    # 1. System clock / date check
    if any(w in q_low for w in ["what time", "current time", "system clock", "what is the date", "today's date"]):
        now = datetime.now()
        context_notes.append(
            f"Local System Clock Readout: {now.strftime('%I:%M:%S %p')} on {now.strftime('%A, %B %d, %Y')}."
        )

    # 2. Weather check
    if WEATHER_REQUEST_PATTERN.search(query):
        city_match = re.search(r"(?:in|for|at)\s+([a-zA-Z\s]{2,25})", query, re.I)
        city_name = city_match.group(1).strip() if city_match else os.getenv("DEFAULT_CITY", "Panaji")
        weather_result = get_weather(city=city_name)
        if weather_result.get("status") == "ONLINE":
            context_notes.append(
                f"Open-Meteo current weather for {weather_result['city']}: "
                f"Temperature={weather_result['temperature']}{weather_result['temp_unit']} "
                f"(feels like {weather_result['feels_like']}{weather_result['temp_unit']}), "
                f"Humidity={weather_result['humidity']}%, "
                f"Wind speed={weather_result['wind_speed']} {weather_result['wind_unit']}, "
                f"Condition={weather_result['condition']}."
            )
        else:
            context_notes.append(
                f"Live weather data for {weather_result['city']} is unavailable. "
                "Do not present fallback or simulated values as current weather."
            )

    # Search only when the user asks for live information or an explicit web lookup.
    if not weather_result and any(hint in q_low for hint in WEB_SEARCH_HINTS):
        web_info = search_web_knowledge(query)
        if web_info:
            context_notes.append(
                "[Optional web reference; use only if it directly answers the latest user request]\n"
                f"{web_info}"
            )

    combined_context = "\n\n".join(context_notes)
    llm_out = query_llm(query, context_data=combined_context)
    if not llm_out.get("online", False):
        return jsonify({"error": llm_out.get("reply", "AI service unavailable")}), 503

    if speak:
        # Strip code blocks before speaking aloud so TTS doesn't read out raw syntax
        spoken_text = re.sub(r"```[\s\S]*?```", " I have displayed the code on your HUD screen, Sir. ", llm_out["reply"])
        voice_engine.speak_async(spoken_text[:450])

    return jsonify({
        "query": query,
        "reply": llm_out["reply"],
        "provider": llm_out["provider"],
        "weather_result": weather_result,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    print("=" * 74)
    print("  J.A.R.V.I.S. // GEMINI CORE EDITION ONLINE (STARK MK-VII HUD)")
    print(f"  Hardware Profile : Salvaged HP 605747-001 Open-Frame Terminal")
    print(f"  HUD Local URL    : http://{host}:{port}")
    print("=" * 74)
    app.run(host=host, port=port, debug=True)
