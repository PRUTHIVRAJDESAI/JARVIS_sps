/* ==========================================================================
   J.A.R.V.I.S. // GEMINI CORE FRONTEND CONTROLLER (jarvis_hud.js)
   Includes Markdown/Code Renderer, PDF/Code Upload & Key Modal
   ========================================================================== */

let voiceEnabled = true;
let voiceRecognition = null;
let isVoiceListening = false;

document.addEventListener("DOMContentLoaded", () => {
  updateSystemTelemetry();
  setInterval(updateSystemTelemetry, 1500);

  fetchWeather("Panaji");

  // Weather scan
  document.getElementById("weather-refresh-btn").addEventListener("click", () => {
    const city = document.getElementById("weather-city-input").value.trim() || "Panaji";
    fetchWeather(city);
  });

  // Command transmit
  document.getElementById("command-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("command-input");
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    sendCommand(q);
  });

  // Preset chips
  document.querySelectorAll(".chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      sendCommand(btn.getAttribute("data-query"));
    });
  });

  // Reset memory & chat stream
  document.getElementById("clear-log-btn").addEventListener("click", async () => {
    await fetch("/api/clear", { method: "POST" });
    document.getElementById("chat-stream").innerHTML = "";
    document.getElementById("active-doc-badge").style.display = "none";
    appendMessage("J.A.R.V.I.S. // GEMINI CORE", "Conversation memory and active file context cleared, Sir.", "jarvis");
  });

  // Voice toggle
  document.getElementById("tts-toggle-btn").addEventListener("click", () => {
    voiceEnabled = !voiceEnabled;
    const btn = document.getElementById("tts-toggle-btn");
    document.getElementById("tts-state").textContent = voiceEnabled ? "ONLINE" : "MUTED";
    document.getElementById("tts-icon").textContent = voiceEnabled ? "🔊" : "🔇";
    btn.classList.toggle("active", voiceEnabled);
    if (!voiceEnabled && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  });

  // Voice input
  document.getElementById("mic-btn").addEventListener("click", startVoiceRecognition);

  // File / PDF Upload button
  const fileInput = document.getElementById("file-upload-input");
  document.getElementById("attach-file-btn").addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", handleFileUpload);

  // AI Key Modal
  const keyModal = document.getElementById("key-modal");
  document.getElementById("open-key-modal-btn").addEventListener("click", () => {
    keyModal.style.display = "flex";
  });
  document.getElementById("close-key-modal-btn").addEventListener("click", () => {
    keyModal.style.display = "none";
  });
  document.getElementById("save-key-btn").addEventListener("click", saveApiKeyConfig);
});

async function updateSystemTelemetry() {
  try {
    const res = await fetch("/api/system");
    const data = await res.json();
    document.getElementById("hud-clock").textContent = data.time_24h;
    document.getElementById("hud-date").textContent = data.date_formatted;
    document.getElementById("uptime-tag").textContent = `UPTIME ${data.uptime}`;
    document.getElementById("cpu-val").textContent = `${data.cpu_percent}%`;
    document.getElementById("cpu-bar").style.width = `${Math.min(data.cpu_percent, 100)}%`;
    document.getElementById("ram-val").textContent = `${data.ram_used_gb} / ${data.ram_total_gb} GB (${data.ram_percent}%)`;
    document.getElementById("ram-bar").style.width = `${Math.min(data.ram_percent, 100)}%`;

    if (data.key_status) {
      const ks = data.key_status;
      const badge = document.getElementById("active-doc-badge");
      if (ks.active_doc) {
        badge.textContent = `📄 ${ks.active_doc}`;
        badge.style.display = "inline-block";
      }
    }
  } catch (err) {
    const now = new Date();
    document.getElementById("hud-clock").textContent = now.toTimeString().split(" ")[0];
  }
}

async function saveApiKeyConfig() {
  const provider = document.getElementById("cfg-provider").value;
  const apiKey = document.getElementById("cfg-api-key").value.trim();
  const modelName = document.getElementById("cfg-model").value.trim();

  if (!apiKey) {
    alert("Please paste a valid API Key first.");
    return;
  }

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, api_key: apiKey, model_name: modelName }),
    });
    const data = await res.json();
    document.getElementById("key-modal").style.display = "none";
    document.getElementById("llm-provider-label").textContent = `BRAIN: ${provider.toUpperCase()} CORE ONLINE`;
    appendMessage(
      "J.A.R.V.I.S. // SYSTEM CONFIG",
      `API Key saved to **.env** and activated for **${provider.toUpperCase()}**. I now have full cloud neural synthesis online, Sir.`,
      "jarvis"
    );
  } catch (err) {
    alert("Failed to save API configuration.");
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  setCoreStatus(`ANALYZING FILE: ${file.name.toUpperCase()}...`);

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (data.error) {
      appendMessage("J.A.R.V.I.S. FILE READER", `Upload error: ${data.error}`, "jarvis");
      return;
    }

    const badge = document.getElementById("active-doc-badge");
    badge.textContent = `📄 ${data.filename}`;
    badge.style.display = "inline-block";

    appendMessage(
      "OPERATOR // FILE UPLOAD",
      `Attached file: **${data.filename}** (${data.chars} characters extracted)`,
      "user"
    );
    appendMessage(
      "J.A.R.V.I.S. DOCUMENT ANALYZER",
      `I have read **${data.filename}** into active memory. Preview:\n\`\`\`text\n${data.preview}\n\`\`\`\nAsk me to summarize it, write code from it, or answer questions about it!`,
      "jarvis"
    );
    setCoreStatus("FILE LOADED IN MEMORY // AWAITING DIRECTIVE");
  } catch (err) {
    appendMessage("J.A.R.V.I.S. FILE READER", "Failed to upload file.", "jarvis");
  }
}

async function fetchWeather(city) {
  try {
    document.getElementById("w-cond").textContent = "SYNCHRONIZING OPEN-METEO...";
    const res = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
    const data = await res.json();
    renderWeather(data);
  } catch (err) {
    document.getElementById("w-cond").textContent = "SENSOR LINK OFFLINE";
  }
}

function renderWeather(data) {
  if (!data) return;
  document.getElementById("w-temp").textContent = `${data.temperature}${data.temp_unit || "°C"}`;
  document.getElementById("w-cond").textContent = data.condition || "NOMINAL";
  const locParts = [data.city, data.country].filter(Boolean).join(", ");
  document.getElementById("w-loc").textContent = `SECTOR: ${locParts.toUpperCase()} (${data.latitude}, ${data.longitude})`;
  document.getElementById("w-hum").textContent = `${data.humidity}${data.humidity_unit || "%"}`;
  document.getElementById("w-wind").textContent = `${data.wind_speed} ${data.wind_unit || "km/h"}`;
  document.getElementById("w-feels").textContent = `${data.feels_like}${data.temp_unit || "°C"}`;
  document.getElementById("w-press").textContent = `${data.pressure} ${data.pressure_unit || "hPa"}`;
  document.getElementById("weather-status-tag").textContent = data.status || "ONLINE";
}

async function sendCommand(queryText) {
  appendMessage("OPERATOR", queryText, "user");
  setCoreStatus("ROUTING QUERY TO GEMINI NEURAL CORE & LOCAL SUBSYSTEMS...");

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText, speak: voiceEnabled }),
    });
    const data = await res.json();
    if (data.error) {
      appendMessage("J.A.R.V.I.S.", `Error: ${data.error}`, "jarvis");
      return;
    }

    if (data.weather_result) {
      renderWeather(data.weather_result);
    }
    document.getElementById("llm-provider-label").textContent = `BRAIN: ${data.provider}`;
    appendMessage("J.A.R.V.I.S. // GEMINI CORE", data.reply, "jarvis");
    speakBrowserFallback(data.reply);
    setCoreStatus("SYSTEM STANDBY // AWAITING DIRECTIVE");
  } catch (err) {
    appendMessage("J.A.R.V.I.S. CORE", "Communication link interrupted. Verify local Flask server.", "jarvis");
    setCoreStatus("LINK INTERRUPTED");
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatMarkdown(mdText) {
  if (!mdText) return "";
  let codeBlocks = [];

  // Extract fenced code blocks ```lang ... ```
  let processed = mdText.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const idx = codeBlocks.length;
    const cleanLang = (lang || "code").toUpperCase();
    const escapedCode = escapeHtml(code.trim());
    const blockHtml = `
      <div class="hud-code-block">
        <div class="hud-code-header">
          <span>${cleanLang} SNIPPET</span>
          <button type="button" class="copy-code-btn" onclick="copyCodeSnippet(this)">COPY CODE</button>
        </div>
        <pre class="hud-code-pre"><code>${escapedCode}</code></pre>
      </div>
    `;
    codeBlocks.push(blockHtml);
    return `@@CODEBLOCK_${idx}@@`;
  });

  processed = escapeHtml(processed);

  // Inline code `...`
  processed = processed.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Bold **...**
  processed = processed.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  // Bullet points
  processed = processed.replace(/^\s*[-*]\s+(.+)$/gm, "<li>$1</li>");
  processed = processed.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");
  // Line breaks
  processed = processed.replace(/\n/g, "<br/>");

  // Restore code blocks
  codeBlocks.forEach((html, idx) => {
    processed = processed.replace(`@@CODEBLOCK_${idx}@@`, html);
  });

  return processed;
}

window.copyCodeSnippet = function(btn) {
  const pre = btn.closest(".hud-code-block").querySelector("pre");
  if (!pre) return;
  navigator.clipboard.writeText(pre.innerText).then(() => {
    const old = btn.textContent;
    btn.textContent = "COPIED ✓";
    setTimeout(() => (btn.textContent = old), 1500);
  });
};

function appendMessage(sender, text, role) {
  const stream = document.getElementById("chat-stream");
  const card = document.createElement("div");
  card.className = `msg-card ${role}`;
  const now = new Date().toTimeString().split(" ")[0];
  card.innerHTML = `
    <div class="msg-meta">
      <span class="msg-sender">${sender}</span>
      <span class="msg-time">${now}</span>
    </div>
    <div class="msg-body">${formatMarkdown(text)}</div>
  `;
  stream.appendChild(card);
  stream.scrollTop = stream.scrollHeight;
}

function setCoreStatus(text) {
  document.getElementById("core-status-text").textContent = text;
}

function speakBrowserFallback(text) {
  if (!voiceEnabled || !text) return;
  const wave = document.getElementById("voice-wave");
  wave.classList.add("speaking");

  // Strip fenced code blocks and markdown characters before browser speech synthesis
  const cleanSpeech = text
    .replace(/```[\s\S]*?```/g, " I have displayed the code on your screen. ")
    .replace(/[*#`_~]/g, "");

  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(cleanSpeech.slice(0, 450));
    utter.rate = 1.05;
    utter.pitch = 0.92;
    const voices = window.speechSynthesis.getVoices();
    const ukVoice = voices.find((v) => v.lang.includes("en-GB") || v.name.toLowerCase().includes("uk") || v.name.toLowerCase().includes("daniel"));
    if (ukVoice) utter.voice = ukVoice;
    utter.onend = () => wave.classList.remove("speaking");
    utter.onerror = () => wave.classList.remove("speaking");
    window.speechSynthesis.speak(utter);
  } else {
    setTimeout(() => wave.classList.remove("speaking"), 3500);
  }
}

function startVoiceRecognition() {
  if (isVoiceListening) {
    voiceRecognition.stop();
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    appendMessage(
      "J.A.R.V.I.S. AUDIO",
      "Voice input is not supported in this browser. Try a current version of Chrome or Edge, and allow microphone access.",
      "jarvis"
    );
    setCoreStatus("VOICE INPUT NOT SUPPORTED");
    return;
  }

  const input = document.getElementById("command-input");
  const button = document.getElementById("mic-btn");
  const originalText = input.value.trim();
  let latestTranscript = "";
  let hadError = false;
  voiceRecognition = new SpeechRecognition();
  voiceRecognition.lang = navigator.language || "en-US";
  voiceRecognition.continuous = false;
  voiceRecognition.interimResults = true;

  voiceRecognition.onstart = () => {
    isVoiceListening = true;
    button.classList.add("listening");
    button.setAttribute("aria-pressed", "true");
    button.setAttribute("aria-label", "Stop voice input");
    button.title = "Stop voice input";
    setCoreStatus("LISTENING // SPEAK NOW OR CLICK MIC TO STOP");
  };

  voiceRecognition.onresult = (event) => {
    latestTranscript = Array.from(event.results)
      .map((result) => result[0].transcript)
      .join(" ")
      .trim();
    input.value = [originalText, latestTranscript].filter(Boolean).join(" ");
  };

  voiceRecognition.onerror = (event) => {
    hadError = true;
    const errors = {
      "not-allowed": "Microphone access was denied. Allow microphone access for this site in your browser settings, then try again.",
      "service-not-allowed": "The browser blocked speech recognition. Allow microphone access and use a secure connection or localhost.",
      "audio-capture": "No microphone was found. Connect or enable a microphone, then try again.",
      "no-speech": "No speech was detected. Click the microphone and try again.",
      network: "Speech recognition needs a network connection. Check your connection and try again."
    };
    const message = errors[event.error] || `Voice input failed (${event.error}). Please try again.`;
    setCoreStatus("VOICE INPUT ERROR");
    appendMessage("J.A.R.V.I.S. AUDIO", message, "jarvis");
  };

  voiceRecognition.onend = () => {
    isVoiceListening = false;
    voiceRecognition = null;
    button.classList.remove("listening");
    button.setAttribute("aria-pressed", "false");
    button.setAttribute("aria-label", "Start voice input");
    button.title = "Start voice input";
    if (!hadError) {
      setCoreStatus(latestTranscript ? "VOICE INPUT READY // REVIEW AND TRANSMIT" : "SYSTEM STANDBY // AWAITING DIRECTIVE");
    }
    if (latestTranscript) {
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  };

  try {
    voiceRecognition.start();
  } catch (error) {
    voiceRecognition = null;
    appendMessage("J.A.R.V.I.S. AUDIO", `Could not start voice input: ${error.message}`, "jarvis");
    setCoreStatus("VOICE INPUT ERROR");
  }
}
