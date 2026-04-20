import math
import cv2
import numpy as np
import mediapipe as mp
import threading
import queue
import pythoncom
import win32com.client
import sys
import time
import random
import json
import pyaudio
import vosk  # Wymaga folderu "model" z polskim modelem Vosk


# ==========================================
# ASYSTENT GŁOSOWY I INTELIGENTNY NASŁUCH (VOSK) - Z va.py
# ==========================================
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
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.stop_stream()
        except Exception as e:
            print("\nBŁĄD INICJALIZACJI VOSK! Upewnij się, że model jest w folderze 'model'.")
            print(f"Szczegóły: {e}\n")
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
                if len(data) == 0: continue
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower()
                    if any(word in text.split() for word in stop_words):
                        self.stop_requested = True
                        break
            except Exception:
                time.sleep(0.5)
                continue

    def speak(self, text):
        self.q.put(text)


# ==========================================
# GŁÓWNY KOD WIZYJNY - Z pol.py (SUROWSZE PROGI)
# ==========================================
CAMERA_FRONT_INDEX = 1
CAMERA_SIDE_INDEX = 0
TARGET_HEIGHT = 480
WINDOW_NAME = "Glute Bridge - Trener"
SHOW_ONLY_SKELETON = False

GREEN = (0, 255, 0);
RED = (0, 0, 255);
WHITE = (255, 255, 255);
YELLOW = (0, 255, 255)

# --- PROGI I TOLERANCJE ---
STAGE2_BRIDGE_MIN = 145
STAGE34_BRIDGE_MIN = 150
STAGE34_HIP_HIGH_MIN = 158
STAGE34_SUPPORT_KNEE_MIN = 70
STAGE34_SUPPORT_KNEE_MAX = 125
STAGE34_SUPPORT_SHIN_MIN = 70
STAGE34_SUPPORT_SHIN_MAX = 110
STAGE34_RAISED_LEG_STRAIGHT_MIN = 160
STAGE34_RAISED_ANKLE_ABOVE_HIP = 90
STAGE34_RAISED_KNEE_ABOVE_HIP = 35

FRONT_PHASE12_HIP_TOL_RATIO = 0.20
FRONT_PHASE34_HIP_TOL_RATIO = 0.24
FRONT_PHASE34_HIP_TOL_MIN = 40
FRONT_PHASE34_ANKLE_DIFF = 22

ERROR_MESSAGES_SIDE = {
    "linia_mostka": "Podnieś wyżej biodra.",
    "biodra_wysoko": "Nie opuszczaj bioder, utrzymaj mostek wysoko.",
    "biodra_na_macie": "Opuść biodra do samej maty.",
    "nogi_ugiete": "Popraw ułożenie stóp, ugnij kolana.",
    "kolano": "Popraw kąt w kolanach.",
    "kolano_podporowe": "Popraw ułożenie nogi podporowej.",
    "piszczel": "Piszczele powinny być ustawione bardziej pionowo.",
    "noga_w_gorze": "Podnieś nogę wyżej.",
    "noga_prosta": "Wyprostuj podniesioną nogę w kolanie.",
    "obie_stopy_na_ziemi": "Postaw obie stopy stabilnie na macie.",
    "glowa_na_macie": "Połóż głowę płasko.",
    "rece_przy_ciele": "Połóż ręce swobodnie wzdłuż ciała."
}

ERROR_MESSAGES_FRONT = {
    "kolana_sym": "Utrzymaj kolana w jednej linii.",
    "kolana_nad_stopami": "Zwróć uwagę, by kolana nie schodziły się do środka.",
    "prawa_noga_w_gorze": "Wyżej prawa noga.",
    "lewa_noga_w_gorze": "Wyżej lewa noga.",
    "biodra_sym": "Nie wykrzywiaj miednicy, trzymaj ją równo."
}

mp_pose = mp.solutions.pose
pose_side = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose_front = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)


# --- FUNKCJE POMOCNICZE (WIZJA) ---
def resize_to_height(frame, target_height=480):
    h, w = frame.shape[:2]
    return cv2.resize(frame, (int(w * target_height / h), target_height))


def to_px(lm, w, h): return int(lm.x * w), int(lm.y * h)


def dist(p1, p2): return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1]);
    bc = (c[0] - b[0], c[1] - b[1])
    nba = math.hypot(*ba);
    nbc = math.hypot(*bc)
    if nba == 0 or nbc == 0: return None
    return math.degrees(math.acos(max(-1.0, min(1.0, (ba[0] * bc[0] + ba[1] * bc[1]) / (nba * nbc)))))


def line_angle_deg(p1, p2): return abs(math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])))


def draw_joint(frame, point, ok, radius=7):
    cv2.circle(frame, point, radius, GREEN if ok else RED, -1)
    cv2.circle(frame, point, radius + 2, WHITE, 1)


def draw_segment(frame, p1, p2, ok, thickness=5):
    cv2.line(frame, p1, p2, GREEN if ok else RED, thickness, cv2.LINE_AA)


def draw_panel(frame, title, status_rows, overall, extra_text=""):
    x0, y0 = 10, 10
    panel_w, panel_h = 390, 40 + 26 * len(status_rows) + 24
    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (20, 20, 20), -1)
    frame = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)
    cv2.putText(frame, title, (x0 + 10, y0 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.72, GREEN if overall else RED, 2,
                cv2.LINE_AA)
    y = y0 + 52
    for label, ok in status_rows:
        cv2.putText(frame, f"{label}: {'OK' if ok else 'ZLE'}", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    GREEN if ok else RED, 2, cv2.LINE_AA)
        y += 24
    if extra_text:
        cv2.putText(frame, extra_text, (x0 + 10, y0 + panel_h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1,
                    cv2.LINE_AA)
    return frame


def get_side_points(landmarks, w, h):
    ids = mp_pose.PoseLandmark
    l_vis = landmarks[ids.LEFT_HIP.value].visibility;
    r_vis = landmarks[ids.RIGHT_HIP.value].visibility
    side = "LEFT" if l_vis >= r_vis else "RIGHT"

    def p(name): return to_px(landmarks[getattr(ids, f"{side}_{name}").value], w, h)

    return {
        "side": side, "ear": p("EAR"), "shoulder": p("SHOULDER"), "elbow": p("ELBOW"), "wrist": p("WRIST"),
        "hip": p("HIP"), "knee": p("KNEE"), "ankle": p("ANKLE"),
        "l_hip": to_px(landmarks[ids.LEFT_HIP.value], w, h), "r_hip": to_px(landmarks[ids.RIGHT_HIP.value], w, h),
        "l_knee": to_px(landmarks[ids.LEFT_KNEE.value], w, h), "r_knee": to_px(landmarks[ids.RIGHT_KNEE.value], w, h),
        "l_ankle": to_px(landmarks[ids.LEFT_ANKLE.value], w, h),
        "r_ankle": to_px(landmarks[ids.RIGHT_ANKLE.value], w, h)
    }


def pick_support_and_raised(points):
    legs = [{"name": "left", "hip": points["l_hip"], "knee": points["l_knee"], "ankle": points["l_ankle"]},
            {"name": "right", "hip": points["r_hip"], "knee": points["r_knee"], "ankle": points["r_ankle"]}]
    support = max(legs, key=lambda l: l["ankle"][1])
    raised = legs[0] if support["name"] == "right" else legs[1]
    return support, raised


def detect_phase_side(points, check_phase, prev_raised_leg=None):
    ear, shoulder, elbow, wrist, hip = points["ear"], points["shoulder"], points["elbow"], points["wrist"], points[
        "hip"]
    support, raised = pick_support_and_raised(points)

    neck_ang = line_angle_deg(shoulder, ear);
    trunk_ang = line_angle_deg(shoulder, hip)
    shin_ang = line_angle_deg(support["knee"], support["ankle"])
    supp_knee_ang = angle(hip, support["knee"], support["ankle"])
    arm_ang = angle(shoulder, elbow, wrist);
    hip_ang = angle(shoulder, hip, support["knee"])

    tulow_lezy = trunk_ang <= 40 or trunk_ang >= 140
    glowa_na_macie = neck_ang <= 40 or neck_ang >= 140

    raised_leg_ang = angle(raised["hip"], raised["knee"], raised["ankle"])
    raised_leg_straight = raised_leg_ang is not None and raised_leg_ang >= STAGE34_RAISED_LEG_STRAIGHT_MIN
    raised_up_strict = (hip[1] - raised["ankle"][1] >= STAGE34_RAISED_ANKLE_ABOVE_HIP) and (
                hip[1] - raised["knee"][1] >= STAGE34_RAISED_KNEE_ABOVE_HIP)
    raised_up_soft = raised["ankle"][1] < hip[1] - 40

    is_bridge2 = hip_ang is not None and hip_ang >= STAGE2_BRIDGE_MIN
    is_bridge34 = hip_ang is not None and hip_ang >= STAGE34_BRIDGE_MIN

    stage1 = {"nogi_ugiete": supp_knee_ang is not None and 50 <= supp_knee_ang <= 145,
              "obie_stopy_na_ziemi": not raised_up_soft, "tulow_lezy": tulow_lezy,
              "biodra_na_macie": hip_ang is not None and hip_ang < 140,
              "rece_przy_ciele": arm_ang is not None and arm_ang >= 145, "glowa_na_macie": glowa_na_macie}
    stage2 = {"linia_mostka": is_bridge2, "kolano": supp_knee_ang is not None and 50 <= supp_knee_ang <= 145,
              "piszczel": shin_ang is not None and 50 <= shin_ang <= 130, "obie_stopy_na_ziemi": not raised_up_soft,
              "rece_przy_ciele": arm_ang is not None and arm_ang >= 145, "glowa_na_macie": glowa_na_macie}
    stage3 = {"linia_mostka": is_bridge34, "biodra_wysoko": hip_ang is not None and hip_ang >= STAGE34_HIP_HIGH_MIN,
              "kolano_podporowe": supp_knee_ang is not None and STAGE34_SUPPORT_KNEE_MIN <= supp_knee_ang <= STAGE34_SUPPORT_KNEE_MAX,
              "piszczel": shin_ang is not None and STAGE34_SUPPORT_SHIN_MIN <= shin_ang <= STAGE34_SUPPORT_SHIN_MAX,
              "noga_w_gorze": raised_up_strict, "noga_prosta": raised_leg_straight,
              "rece_przy_ciele": arm_ang is not None and arm_ang >= 145, "glowa_na_macie": glowa_na_macie}
    stage4 = {**stage3, "zmiana_nogi": (raised["name"] != prev_raised_leg) if prev_raised_leg else False}

    metrics = {"support": support, "raised": raised, "support_knee_angle": supp_knee_ang, "hip_angle": hip_ang,
               "raised_ankle_above_hip": hip[1] - raised["ankle"][1],
               "raised_knee_above_hip": hip[1] - raised["knee"][1]}
    phases = {1: stage1, 2: stage2, 3: stage3, 4: stage4}
    curr_stage = phases.get(check_phase, {})
    return curr_stage, all(curr_stage.values()), metrics


def evaluate_front(points, check_phase):
    hip_w = dist(points["l_hip"], points["r_hip"]);
    knee_w = dist(points["l_knee"], points["r_knee"]);
    ankle_w = dist(points["l_ankle"], points["r_ankle"])
    hip_l = abs(points["l_hip"][1] - points["r_hip"][1])
    tol_h = max(FRONT_PHASE34_HIP_TOL_MIN if check_phase > 2 else 25,
                hip_w * (FRONT_PHASE34_HIP_TOL_RATIO if check_phase > 2 else FRONT_PHASE12_HIP_TOL_RATIO))

    if check_phase <= 2:
        checks = {"biodra_sym": hip_l <= tol_h, "kolana_sym": abs(points["l_knee"][1] - points["r_knee"][1]) <= 35,
                  "kolana_nad_stopami": abs(points["l_knee"][0] - points["l_ankle"][0]) <= 40 and abs(
                      points["r_knee"][0] - points["r_ankle"][0]) <= 40}
    elif check_phase == 3:
        checks = {"biodra_sym": hip_l <= tol_h,
                  "prawa_noga_w_gorze": (points["l_ankle"][1] - points["r_ankle"][1]) >= FRONT_PHASE34_ANKLE_DIFF}
    else:
        checks = {"biodra_sym": hip_l <= tol_h,
                  "lewa_noga_w_gorze": (points["r_ankle"][1] - points["l_ankle"][1]) >= FRONT_PHASE34_ANKLE_DIFF}
    return checks, all(checks.values())


def draw_side_skeleton(frame, p, checks, metrics, check_phase):
    mostek_ok = checks.get("linia_mostka", checks.get("tulow_lezy", True))
    trunk_ok = mostek_ok and checks.get("biodra_wysoko", True)
    kolano_ok = checks.get("kolano_podporowe", checks.get("kolano", checks.get("nogi_ugiete", True)))

    draw_segment(frame, p["shoulder"], p["hip"], trunk_ok)
    draw_segment(frame, p["hip"], metrics["support"]["knee"], kolano_ok)
    draw_segment(frame, metrics["support"]["knee"], metrics["support"]["ankle"], checks.get("piszczel", True))
    draw_segment(frame, p["shoulder"], p["elbow"], checks.get("rece_przy_ciele", True))
    draw_segment(frame, p["elbow"], p["wrist"], checks.get("rece_przy_ciele", True))
    draw_segment(frame, p["shoulder"], p["ear"], checks.get("glowa_na_macie", True))

    if check_phase in (3, 4):
        noga_ok = checks.get("noga_prosta", False) and checks.get("noga_w_gorze", False)
        draw_segment(frame, metrics["raised"]["hip"], metrics["raised"]["knee"], noga_ok)
        draw_segment(frame, metrics["raised"]["knee"], metrics["raised"]["ankle"], noga_ok)


# ==========================================
# GŁÓWNY PROGRAM (ŁĄCZENIE LOGIKI)
# ==========================================
def main():
    assistant = VoiceAssistant()
    cap_front = cv2.VideoCapture(CAMERA_FRONT_INDEX);
    cap_side = cv2.VideoCapture(CAMERA_SIDE_INDEX)
    if not cap_side.isOpened(): return

    state, reps, frames_held, prev_raised_leg = 1, 0, 0, None
    consecutive_errors, error_cooldown, skeleton_only = 0, 0, SHOW_ONLY_SKELETON

    assistant.speak("Cześć, zaczynajmy. Połóż się na macie. Słucham komendy stop tylko podczas odpoczynku.")

    while True:
        assistant.listen_active = (state == 1)
        if assistant.stop_requested:
            assistant.speak("Dziękuję za wspólny trening, świetna robota!")
            cv2.waitKey(3000);
            break

        ret_s, frame_side = cap_side.read()
        if not ret_s: continue
        frame_side = resize_to_height(frame_side, TARGET_HEIGHT)

        ret_f, frame_front = cap_front.read()
        if ret_f:
            frame_front = cv2.rotate(frame_front, cv2.ROTATE_90_CLOCKWISE)
            frame_front = resize_to_height(frame_front, TARGET_HEIGHT)
        else:
            frame_front = np.zeros((TARGET_HEIGHT, 400, 3), dtype=np.uint8)

        # Przetwarzanie BOK
        rgb_s = cv2.cvtColor(frame_side, cv2.COLOR_BGR2RGB);
        res_s = pose_side.process(rgb_s)
        view_side = frame_side.copy()
        if skeleton_only: view_side[:] = 0

        ok_side_status = False;
        checks_side = {};
        metrics = {}
        if res_s.pose_landmarks:
            p_s = get_side_points(res_s.pose_landmarks.landmark, view_side.shape[1], TARGET_HEIGHT)
            checks_side, ok_side_status, metrics = detect_phase_side(p_s, state, prev_raised_leg)
            draw_side_skeleton(view_side, p_s, checks_side, metrics, state)
            extra = f"biodro={int(metrics['hip_angle'] or 0)}  kol={int(metrics['support_knee_angle'] or 0)}"
            view_side = draw_panel(view_side, f"BOK: FAZA {state}", checks_side.items(), ok_side_status, extra)

        # Przetwarzanie PRZÓD
        ok_front_status = True;
        checks_front = {}
        view_front = frame_front.copy()
        if skeleton_only: view_front[:] = 0
        rgb_f = cv2.cvtColor(frame_front, cv2.COLOR_BGR2RGB);
        res_f = pose_front.process(rgb_f)
        if res_f.pose_landmarks:
            ids = mp_pose.PoseLandmark;
            landmarks = res_f.pose_landmarks.landmark
            p_f = {k: to_px(landmarks[getattr(ids, k.upper()).value], view_front.shape[1], TARGET_HEIGHT) for k in
                   ["l_hip", "r_hip", "l_knee", "r_knee", "l_ankle", "r_ankle"]}
            checks_front, ok_front_status = evaluate_front(p_f, state)
            view_front = draw_panel(view_front, f"PRZOD: FAZA {state}", checks_front.items(), ok_front_status)

        # Logika przejść (Maszyna Stanów z losowymi tekstami z va.py)
        if ok_side_status and ok_front_status:
            frames_held += 1;
            consecutive_errors = 0
            if frames_held >= (15 if state == 1 else 7):
                if state == 1:
                    assistant.speak(
                        random.choice(["Okej, teraz podnieś biodra.", "Świetnie, wypchnij miednicę w górę."]))
                    state = 2
                elif state == 2:
                    assistant.speak(random.choice(["Dobra robota, podnieś prawą nogę.", "Prawa noga w górę."]))
                    state = 3
                elif state == 3:
                    prev_raised_leg = metrics["raised"]["name"]
                    assistant.speak("Super. Teraz zmień nogę, lewa w górę.")
                    state = 4
                elif state == 4:
                    reps += 1
                    assistant.speak(f"Dobra robota, mamy {reps} powtórzeń. Opuść biodra.")
                    state = 1;
                    prev_raised_leg = None
                frames_held = 0;
                error_cooldown = 0
        else:
            frames_held = max(0, frames_held - 1);
            consecutive_errors += 1
            if consecutive_errors > 40 and error_cooldown == 0:
                for d, c in [(checks_side, ERROR_MESSAGES_SIDE), (checks_front, ERROR_MESSAGES_FRONT)]:
                    failed = [k for k, v in d.items() if not v]
                    if failed and failed[0] in c:
                        assistant.speak(c[failed[0]])
                        error_cooldown = 150;
                        break

        # Renderowanie
        combined = cv2.hconcat([view_side, view_front])
        cv2.putText(combined, f"POWTORZENIA: {reps}", (view_side.shape[1] - 230, TARGET_HEIGHT - 40),
                    cv2.FONT_HERSHEY_TRIPLEX, 0.7, YELLOW, 1)
        if assistant.listen_active:
            cv2.putText(combined, "[VOSK SŁUCHA - 'stop']", (20, TARGET_HEIGHT - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        YELLOW, 1)
        cv2.imshow(WINDOW_NAME, combined)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('n'):
            assistant.stop_requested = True
        elif key == ord('m'):
            skeleton_only = not skeleton_only

    cap_front.release();
    cap_side.release();
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()