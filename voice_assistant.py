import threading
import queue
import pythoncom
import win32com.client
import sys
import time
import json
import pyaudio
import vosk


class VoiceAssistant:
    def __init__(self):
        self.q = queue.Queue()
        self.stop_requested = False
        self.listen_active = False

        self.speak_thread = threading.Thread(target=self._speak_worker, daemon=True)
        self.speak_thread.start()

        self.listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self.listen_thread.start()

    def _speak_worker(self):
        if sys.platform == 'win32':
            try:
                pythoncom.CoInitialize()
            except Exception as e:
                print(f"Brak biblioteki pywin32: {e}")

        speaker = win32com.client.Dispatch("SAPI.SpVoice")

        try:
            voices = speaker.GetVoices()
            for i in range(voices.Count):
                voice = voices.Item(i)
                desc = voice.GetDescription().lower()
                if "polish" in desc or "polski" in desc or "paulina" in desc or "pl-" in desc:
                    speaker.Voice = voice
                    break
        except Exception as e:
            print(f"Nie udało się ustawić polskiego głosu: {e}")

        speaker.Rate = 3

        while True:
            task = self.q.get()
            if task is None:
                break
            try:
                speaker.Speak(task)
            except Exception as e:
                print(f"Błąd mówienia: {e}")
            self.q.task_done()

    def _listen_worker(self):
        stop_words = ["stop", "koniec", "dość", "wystarczy", "kończymy"]

        try:
            model = vosk.Model("model")
            recognizer = vosk.KaldiRecognizer(model, 16000)

            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            stream.stop_stream()
        except Exception as e:
            print("BŁĄD INICJALIZACJI VOSK!")
            print("Upewnij się, że pobrałaś polski model Vosk i umieściłaś go w folderze o nazwie 'model'")
            print(f"Szczegóły: {e}")
            return

        while not self.stop_requested:
            if not self.listen_active:
                if stream.is_active():
                    stream.stop_stream()
                time.sleep(0.2)
                continue

            if not stream.is_active():
                stream.start_stream()
                try:
                    stream.read(stream.get_read_available(), exception_on_overflow=False)
                except:
                    pass

            try:
                data = stream.read(4000, exception_on_overflow=False)
                if len(data) == 0:
                    continue

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower()

                    if text:
                        if any(word in text.split() for word in stop_words) or any(word in text for word in stop_words):
                            self.stop_requested = True
                            break
            except Exception:
                time.sleep(0.5)
                continue

    def speak(self, text):
        self.q.put(text)