# J.A.R.V.I.S. AI Screen Project (Stark Mark-VII HUD)

Built specifically for the **Open-Frame Salvaged HP Laptop Project** (`Motherboard 605747-001`, 2010–2011 Intel CPU, 4GB DDR3 RAM, 320GB HDD, direct LVDS LCD panel).

## Architecture & Locked-In Project Decisions Implemented
1. **Body vs. Cloud Brain Architecture**:
   - **Body (Local Hardware)**: Handles text input (plus optional voice input hook), Iron Man J.A.R.V.I.S. holographic HUD display, local system clock, document/code file reading, and offline `pyttsx3` text-to-speech voice output.
   - **Brain (Cloud LLM over Wi-Fi)**: Routes general Q&A to the **Claude API** (`claude-3-5-haiku-latest` for ~$1–5/month hobby usage), while also supporting zero-cost free-tier keys (**Google Gemini** or **Groq**) and an **Offline Local Core** fallback.
2. **System Clock**: Read directly from the host system clock (`datetime` & `psutil` hardware telemetry).
3. **Weather Telemetry**: Powered by **Open-Meteo API** (100% free, no signup, no API key required) — displays live temperature, relative humidity, wind speed, feels-like temperature, atmospheric pressure, and conditions.

## Quick Start Instructions
1. Extract `jarvis_ai_screen_project.zip` and open a terminal in the folder.
2. Copy `.env.example` to `.env` and add your `ANTHROPIC_API_KEY` (or `GEMINI_API_KEY` / `GROQ_API_KEY` for free tier). *Note: The app works immediately in Local Core mode even before adding an API key!*
3. Install dependencies and run:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
4. Open `http://127.0.0.1:5000` in your browser (press **F11** for full-screen open-frame kiosk mode).
