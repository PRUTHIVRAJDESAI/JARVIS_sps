"""
Offline Text-to-Speech (TTS) Service
Fulfills Section 4 of Project Spec:
- Output method: Text on screen + spoken voice output (offline text-to-speech) from the start.
- Uses pyttsx3 in a non-blocking daemon thread so the Flask server never hangs.
"""
import os
import threading

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except Exception:
    PYTTSX3_AVAILABLE = False


class JarvisVoiceEngine:
    def __init__(self):
        self.enabled = os.getenv("ENABLE_SERVER_TTS", "true").lower() == "true"
        self.rate = int(os.getenv("TTS_RATE", "175"))
        self.volume = float(os.getenv("TTS_VOLUME", "1.0"))
        self._lock = threading.Lock()

    def speak_async(self, text: str):
        """Speak text aloud on the host machine using offline pyttsx3 without blocking."""
        if not self.enabled or not PYTTSX3_AVAILABLE or not text:
            return False

        clean_text = text.replace("*", "").replace("#", "").replace("`", "")
        thread = threading.Thread(target=self._speak_worker, args=(clean_text,), daemon=True)
        thread.start()
        return True

    def _speak_worker(self, text: str):
        with self._lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                voices = engine.getProperty("voices")
                # Prefer a British / clear English voice if available on the OS
                for v in voices:
                    v_name = (v.name or "").lower()
                    if "david" in v_name or "george" in v_name or "uk" in v_name or "english" in v_name:
                        engine.setProperty("voice", v.id)
                        break
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception:
                pass


voice_engine = JarvisVoiceEngine()
