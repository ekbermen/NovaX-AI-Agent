import os
import time
import threading
from urllib.parse import quote

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import mainthread

from google import genai
from google.genai import types
from elevenlabs.client import ElevenLabs
import speech_recognition as sr

from jnius import autoclass

Intent = autoclass('android.content.Intent')
Uri = autoclass('android.net.Uri')
PythonActivity = autoclass('org.kivy.android.PythonActivity')

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "BURAYA_GEMINI_API_KEY_YAZIN")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "BURAYA_ELEVENLABS_API_KEY_YAZIN")
VOICE_ID = "BURAYA_ELEVENLABS_VOICE_ID_YAZIN"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def _start_view_intent(url: str):
    activity = PythonActivity.mActivity
    intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
    activity.startActivity(intent)


def open_website(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    _start_view_intent(url)
    return f"{url} açıldı."


def search_google(query: str):
    search_url = f"https://www.google.com/search?q={quote(query)}"
    _start_view_intent(search_url)
    return f"Google-da '{query}' axtarıldı."


def open_camera():
    activity = PythonActivity.mActivity
    intent = Intent("android.media.action.IMAGE_CAPTURE")
    activity.startActivity(intent)
    return "Arxa kamera açıldı."


def open_live_camera():
    activity = PythonActivity.mActivity
    intent = Intent("android.media.action.VIDEO_CAPTURE")
    intent.putExtra("android.intent.extras.CAMERA_FACING", 1)
    activity.startActivity(intent)
    return "Ön canlı kamera işə düşdü cənab."


def get_battery_status():
    try:
        context = PythonActivity.mActivity
        BatteryManager = autoclass('android.os.BatteryManager')
        bm = context.getSystemService("batterymanager")
        level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        return f"Batareya səviyyəsi hazırda faizdə {level}-dir."
    except Exception:
        return "Batareya məlumatı oxuna bilmədi."


def toggle_flashlight(state: str = "on"):
    try:
        context = PythonActivity.mActivity
        CameraManager = autoclass('android.hardware.camera2.CameraManager')
        cm = context.getSystemService("camera")
        cam_id = cm.getCameraIdList()[0]
        cm.setTorchMode(cam_id, state.lower() == "on")
        return "Fənər yandırıldı cənab." if state.lower() == "on" else "Fənər söndürüldü cənab."
    except Exception:
        return "Fənər idarə oluna bilmədi cənab."


def open_maps(location: str):
    maps_url = f"https://www.google.com/maps/search/{quote(location)}"
    _start_view_intent(maps_url)
    return f"Xəritədə {location} axtarılır."


def play_music(song_name: str = ""):
    if song_name:
        music_url = f"https://music.youtube.com/search?q={quote(song_name)}"
    else:
        music_url = "https://music.youtube.com"
    _start_view_intent(music_url)
    return f"{song_name} üçün musiqi platforması açıldı."


tools_list = [
    open_website,
    search_google,
    open_camera,
    open_live_camera,
    get_battery_status,
    toggle_flashlight,
    open_maps,
    play_music,
]

SYSTEM_PROMPT = """
Sən NOVAX v5.0 süni intellekt köməkçisisən. İstifadəçiyə həmişə 'Cənab' deyə müraciət et. Cavabların qısa, dəqiq və ağıllı olmalıdır.
Tələb olunduqda aşağıdakı alətlərdən istifadə et:
- open_website: Sayt açmaq üçün
- search_google: Google axtarışı üçün
- open_camera: Foto çəkmək üçün arxa kameranı açmaq
- open_live_camera: Canlı izləmə üçün ön (selfie) kameranı açmaq
- get_battery_status: Batareya faizini öyrənmək
- toggle_flashlight: Fənəri yandırmaq/söndürmək
- open_maps: Xəritədə yer axtarmaq
- play_music: Musiqi oxutmaq
Cavablarında emoji, ulduz (*) və ya simvollar İSTİFADƏ ETMƏ.
"""


class NovaxUI(BoxLayout):
    pass


class NovaxApp(App):
    def build(self):
        self.orientation = "vertical"
        root = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.status_label = Label(text="NOVAX v5.0 hazır cənab.\nDinləmək üçün düyməyə basın.")
        root.add_widget(self.status_label)

        listen_btn = Button(text="Dinlə", size_hint=(1, 0.3))
        listen_btn.bind(on_press=self.on_listen_pressed)
        root.add_widget(listen_btn)

        return root

    def on_listen_pressed(self, instance):
        threading.Thread(target=self.listen_and_respond, daemon=True).start()

    @mainthread
    def set_status(self, text):
        self.status_label.text = text

    def speak(self, text):
        self.set_status(text)
        try:
            audio = eleven_client.generate(text=text, voice=VOICE_ID, model="eleven_multilingual_v2")
            out_path = "/sdcard/novax_voice.mp3"
            with open(out_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            _start_view_intent("file://" + out_path)
        except Exception as e:
            print(f"[Səs Xətası]: {e}")

    def listen_audio(self, prompt_text=None):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            if prompt_text:
                self.set_status(prompt_text)
            r.adjust_for_ambient_noise(source, duration=0.4)
            try:
                audio = r.listen(source, timeout=6, phrase_time_limit=8)
                return r.recognize_google(audio, language="tr-TR").lower()
            except Exception:
                return ""

    def listen_and_respond(self):
        user_command = self.listen_audio("Əmrinizi bildirin...")
        if not user_command:
            self.speak("Səsinizi eşidə bilmədim cənab.")
            return

        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_command,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=tools_list,
                    temperature=0.7,
                ),
            )

            if response.function_calls:
                for call in response.function_calls:
                    fn_name = call.name
                    fn_args = call.args
                    fn_map = {
                        "open_website": open_website,
                        "search_google": search_google,
                        "open_camera": lambda: open_camera(),
                        "open_live_camera": lambda: open_live_camera(),
                        "get_battery_status": lambda: get_battery_status(),
                        "toggle_flashlight": toggle_flashlight,
                        "open_maps": open_maps,
                        "play_music": play_music,
                    }
                    if fn_name in fn_map:
                        fn = fn_map[fn_name]
                        result = fn(**fn_args) if fn_args and fn_name not in (
                            "open_camera", "open_live_camera", "get_battery_status"
                        ) else fn()
                        self.speak(result)
            else:
                self.speak(response.text)
        except Exception as e:
            self.speak(f"Xəta baş verdi cənab: {e}")


if __name__ == "__main__":
    NovaxApp().run()
