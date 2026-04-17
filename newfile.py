import math
import cv2
import mediapipe as mp

# Indeksy kamer (Upewnij się, że pasują do Twojego sprzętu)
CAMERA_FRONT_INDEX = 0
CAMERA_SIDE_INDEX = 1
TARGET_HEIGHT = 480
WINDOW_NAME = "Glute Bridge - Trener (BOK + PRZOD)"
SHOW_ONLY_SKELETON = False

GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)

mp_pose = mp.solutions.pose
pose_side = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
pose_front = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


def resize_to_height(frame, target_height=480):
    h, w = frame.shape[:2]
    new_width = int(w * target_height / h)
    return cv2.resize(frame, (new_width, target_height))


def to_px(lm, w, h):
    return int(lm.x * w), int(lm.y * h)


def dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    nba = math.hypot(*ba)
    nbc = math.hypot(*bc)
    if nba == 0 or nbc == 0:
        return None
    cosang = max(-1.0, min(1.0, (ba[0] * bc[0] + ba[1] * bc[1]) / (nba * nbc)))
    return math.degrees(math.acos(cosang))


def line_angle_deg(p1, p2):
    return abs(math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])))


def point_line_distance(point, a, b):
    ax, ay = a
    bx, by = b
    px, py = point
    den = math.hypot(bx - ax, by - ay)
    if den == 0:
        return 0
    return abs((by - ay) * px - (bx - ax) * py + bx * ay - by * ax) / den


def draw_joint(frame, point, ok, radius=7):
    color = GREEN if ok else RED
    cv2.circle(frame, point, radius, color, -1)
    cv2.circle(frame, point, radius + 2, WHITE, 1)


def draw_segment(frame, p1, p2, ok, thickness=5):
    color = GREEN if ok else RED
    cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)


def draw_panel(frame, title, status_rows, overall, extra_text=""):
    x0, y0 = 10, 10
    panel_w = 350
    panel_h = 40 + 26 * len(status_rows) + 24
    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (20, 20, 20), -1)
    frame = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)
    cv2.rectangle(frame, (x0, y0), (x0 + panel_w, y0 + panel_h), (80, 80, 80), 1)

    title_color = GREEN if overall else RED
    cv2.putText(frame, title, (x0 + 10, y0 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.72, title_color, 2, cv2.LINE_AA)

    y = y0 + 52
    for label, ok in status_rows:
        color = GREEN if ok else RED
        status = "OK" if ok else "ZLE"
        cv2.putText(frame, f"{label}: {status}", (x0 + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)
        y += 24

    if extra_text:
        cv2.putText(frame, extra_text, (x0 + 10, y0 + panel_h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1,
                    cv2.LINE_AA)
    return frame


def visible_side_name(landmarks):
    ids = mp_pose.PoseLandmark
    left_vis = landmarks[ids.LEFT_SHOULDER.value].visibility + landmarks[ids.LEFT_HIP.value].visibility + landmarks[
        ids.LEFT_KNEE.value].visibility
    right_vis = landmarks[ids.RIGHT_SHOULDER.value].visibility + landmarks[ids.RIGHT_HIP.value].visibility + landmarks[
        ids.RIGHT_KNEE.value].visibility
    return "LEFT" if left_vis >= right_vis else "RIGHT"


def get_side_points(landmarks, w, h):
    ids = mp_pose.PoseLandmark
    side = visible_side_name(landmarks)
    sfx = "LEFT" if side == "LEFT" else "RIGHT"

    def p(name): return to_px(landmarks[getattr(ids, f"{sfx}_{name}").value], w, h)

    return {
        "side": side, "ear": p("EAR"), "shoulder": p("SHOULDER"), "elbow": p("ELBOW"), "wrist": p("WRIST"),
        "hip": p("HIP"), "knee": p("KNEE"), "ankle": p("ANKLE"), "heel": p("HEEL"), "foot": p("FOOT_INDEX"),
        "l_hip": to_px(landmarks[ids.LEFT_HIP.value], w, h), "r_hip": to_px(landmarks[ids.RIGHT_HIP.value], w, h),
        "l_knee": to_px(landmarks[ids.LEFT_KNEE.value], w, h), "r_knee": to_px(landmarks[ids.RIGHT_KNEE.value], w, h),
        "l_ankle": to_px(landmarks[ids.LEFT_ANKLE.value], w, h),
        "r_ankle": to_px(landmarks[ids.RIGHT_ANKLE.value], w, h),
    }


def get_front_points(landmarks, w, h):
    ids = mp_pose.PoseLandmark
    return {
        "l_shoulder": to_px(landmarks[ids.LEFT_SHOULDER.value], w, h),
        "r_shoulder": to_px(landmarks[ids.RIGHT_SHOULDER.value], w, h),
        "l_elbow": to_px(landmarks[ids.LEFT_ELBOW.value], w, h),
        "r_elbow": to_px(landmarks[ids.RIGHT_ELBOW.value], w, h),
        "l_wrist": to_px(landmarks[ids.LEFT_WRIST.value], w, h),
        "r_wrist": to_px(landmarks[ids.RIGHT_WRIST.value], w, h),
        "l_hip": to_px(landmarks[ids.LEFT_HIP.value], w, h), "r_hip": to_px(landmarks[ids.RIGHT_HIP.value], w, h),
        "l_knee": to_px(landmarks[ids.LEFT_KNEE.value], w, h), "r_knee": to_px(landmarks[ids.RIGHT_KNEE.value], w, h),
        "l_ankle": to_px(landmarks[ids.LEFT_ANKLE.value], w, h),
        "r_ankle": to_px(landmarks[ids.RIGHT_ANKLE.value], w, h),
    }


def pick_support_and_raised(points):
    legs = [
        {"name": "left", "hip": points["l_hip"], "knee": points["l_knee"], "ankle": points["l_ankle"]},
        {"name": "right", "hip": points["r_hip"], "knee": points["r_knee"], "ankle": points["r_ankle"]}
    ]
    support = max(legs, key=lambda leg: leg["ankle"][1])
    raised = legs[0] if support["name"] == "right" else legs[1]
    return support, raised


def detect_phase_side(points, check_phase, prev_raised_leg=None):
    ear, shoulder, elbow, wrist, hip = points["ear"], points["shoulder"], points["elbow"], points["wrist"], points[
        "hip"]
    support, raised = pick_support_and_raised(points)
    support_knee, support_ankle = support["knee"], support["ankle"]

    neck_angle = line_angle_deg(shoulder, ear)
    trunk_angle = line_angle_deg(shoulder, hip)
    support_thigh_angle = line_angle_deg(hip, support_knee)
    support_shin_angle = line_angle_deg(support_knee, support_ankle)
    support_knee_angle = angle(hip, support_knee, support_ankle)
    arm_angle = angle(shoulder, elbow, wrist)

    hip_to_line = point_line_distance(hip, shoulder, support_knee)

    tulow_lezy = trunk_angle is not None and (trunk_angle <= 40 or trunk_angle >= 140)
    glowa_na_macie = neck_angle is not None and (neck_angle <= 40 or neck_angle >= 140)

    raised_leg_up = raised["ankle"][1] < hip[1] - 40
    raised_leg_straight = False
    raised_leg_angle = angle(raised["hip"], raised["knee"], raised["ankle"])
    if raised_leg_angle is not None:
        raised_leg_straight = raised_leg_angle >= 150

    stage1 = {
        "nogi_ugiete": support_knee_angle is not None and 50 <= support_knee_angle <= 145,
        "obie_stopy_na_ziemi": not raised_leg_up,
        "tulow_lezy": tulow_lezy,
        "rece_przy_ciele": arm_angle is not None and arm_angle >= 145,
        "glowa_na_macie": glowa_na_macie,
    }

    stage2 = {
        "linia_mostka": trunk_angle is not None and support_thigh_angle is not None and abs(
            trunk_angle - support_thigh_angle) <= 25,
        "kolano": support_knee_angle is not None and 50 <= support_knee_angle <= 145,
        "piszczel": support_shin_angle is not None and 50 <= support_shin_angle <= 130,
        "obie_stopy_na_ziemi": not raised_leg_up,
        "rece_przy_ciele": arm_angle is not None and arm_angle >= 145,
        "glowa_na_macie": glowa_na_macie,
    }

    stage3 = {
        "linia_mostka": stage2["linia_mostka"],
        "kolano_podporowe": stage2["kolano"],
        "piszczel": stage2["piszczel"],
        "noga_w_gorze": raised_leg_up,
        "noga_prosta": raised_leg_straight,
        "rece_przy_ciele": stage2["rece_przy_ciele"],
        "glowa_na_macie": glowa_na_macie,
    }

    metrics = {
        "support_knee_angle": support_knee_angle,
        "trunk_angle": trunk_angle,
        "support_thigh_angle": support_thigh_angle,
        "raised_leg_angle": raised_leg_angle,
        "hip_to_line": hip_to_line,
        "support": support,
        "raised": raised,
    }

    if check_phase == 1:
        return stage1, all(stage1.values()), metrics
    elif check_phase == 2:
        return stage2, all(stage2.values()), metrics
    elif check_phase == 3:
        return stage3, all(stage3.values()), metrics
    elif check_phase == 4:
        stage4 = stage3.copy()
        if prev_raised_leg is not None:
            stage4["zmiana_nogi"] = (raised["name"] != prev_raised_leg)
        else:
            stage4["zmiana_nogi"] = False
        return stage4, all(stage4.values()), metrics

    return {}, False, metrics


def evaluate_front(points, check_phase):
    hip_width = dist(points["l_hip"], points["r_hip"])
    knee_width = dist(points["l_knee"], points["r_knee"])
    ankle_width = dist(points["l_ankle"], points["r_ankle"])

    hip_level = abs(points["l_hip"][1] - points["r_hip"][1])

    tol_h = max(25, hip_width * 0.20)
    tol_k = max(35, knee_width * 0.25 if knee_width > 0 else 35)
    tol_mid = max(40, ankle_width * 0.30 if ankle_width > 0 else 40)

    knee_over_ankle_l = abs(points["l_knee"][0] - points["l_ankle"][0])
    knee_over_ankle_r = abs(points["r_knee"][0] - points["r_ankle"][0])

    base = {"biodra_sym": hip_level <= tol_h}

    if check_phase in (1, 2):
        knee_level = abs(points["l_knee"][1] - points["r_knee"][1])
        checks = {
            **base,
            "kolana_sym": knee_level <= tol_k,
            "kolana_nad_stopami": knee_over_ankle_l <= tol_mid and knee_over_ankle_r <= tol_mid
        }
    elif check_phase == 3:
        prawa_wyzej = points["r_ankle"][1] < points["l_ankle"][1] - 30
        checks = {**base, "prawa_noga_w_gorze": prawa_wyzej}
    elif check_phase == 4:
        lewa_wyzej = points["l_ankle"][1] < points["r_ankle"][1] - 30
        checks = {**base, "lewa_noga_w_gorze": lewa_wyzej}

    metrics = {"ratio": 0}
    return checks, metrics, all(checks.values())


def draw_phase1_2_front(frame, p, checks):
    knees_ok = checks.get("kolana_sym", True) and checks.get("kolana_nad_stopami", True)
    draw_segment(frame, p["l_hip"], p["l_knee"], knees_ok)
    draw_segment(frame, p["r_hip"], p["r_knee"], knees_ok)
    draw_segment(frame, p["l_knee"], p["l_ankle"], knees_ok)
    draw_segment(frame, p["r_knee"], p["r_ankle"], knees_ok)
    for name in ["l_knee", "r_knee", "l_ankle", "r_ankle"]:
        draw_joint(frame, p[name], knees_ok)


def draw_phase1(frame, p, checks):
    draw_segment(frame, p["shoulder"], p["hip"], checks.get("tulow_lezy", False))
    draw_segment(frame, p["hip"], p["knee"], checks.get("nogi_ugiete", False))
    draw_segment(frame, p["knee"], p["ankle"], checks.get("nogi_ugiete", False))
    draw_segment(frame, p["shoulder"], p["elbow"], checks.get("rece_przy_ciele", False))
    draw_segment(frame, p["elbow"], p["wrist"], checks.get("rece_przy_ciele", False))
    draw_segment(frame, p["shoulder"], p["ear"], checks.get("glowa_na_macie", False))

    draw_joint(frame, p["shoulder"],
               checks.get("tulow_lezy", False) and checks.get("rece_przy_ciele", False) and checks.get("glowa_na_macie",
                                                                                                       False))
    draw_joint(frame, p["hip"], checks.get("tulow_lezy", False))
    draw_joint(frame, p["knee"], checks.get("nogi_ugiete", False))
    draw_joint(frame, p["ankle"], checks.get("nogi_ugiete", False))
    draw_joint(frame, p["elbow"], checks.get("rece_przy_ciele", False))
    draw_joint(frame, p["wrist"], checks.get("rece_przy_ciele", False))
    draw_joint(frame, p["ear"], checks.get("glowa_na_macie", False))


def draw_phase2(frame, p, checks):
    draw_segment(frame, p["shoulder"], p["hip"], checks.get("linia_mostka", False))
    draw_segment(frame, p["hip"], p["knee"], checks.get("linia_mostka", False))
    draw_segment(frame, p["knee"], p["ankle"], checks.get("piszczel", False))
    draw_segment(frame, p["shoulder"], p["elbow"], checks.get("rece_przy_ciele", False))
    draw_segment(frame, p["elbow"], p["wrist"], checks.get("rece_przy_ciele", False))
    draw_segment(frame, p["shoulder"], p["ear"], checks.get("glowa_na_macie", False))

    draw_joint(frame, p["shoulder"],
               checks.get("linia_mostka", False) and checks.get("rece_przy_ciele", False) and checks.get(
                   "glowa_na_macie", False))
    draw_joint(frame, p["hip"], checks.get("linia_mostka", False))
    draw_joint(frame, p["knee"], checks.get("kolano", False))
    draw_joint(frame, p["ankle"], checks.get("piszczel", False))
    draw_joint(frame, p["elbow"], checks.get("rece_przy_ciele", False))
    draw_joint(frame, p["wrist"], checks.get("rece_przy_ciele", False))
    draw_joint(frame, p["ear"], checks.get("glowa_na_macie", False))


def draw_phase3(frame, p, checks, raised):
    draw_segment(frame, p["shoulder"], p["hip"], checks.get("linia_mostka", False))
    draw_segment(frame, p["hip"], p["knee"], checks.get("linia_mostka", False))
    draw_segment(frame, p["knee"], p["ankle"], checks.get("piszczel", False))
    draw_segment(frame, p["shoulder"], p["elbow"], checks.get("rece_przy_ciele", False))
    draw_segment(frame, p["elbow"], p["wrist"], checks.get("rece_przy_ciele", False))
    draw_segment(frame, p["shoulder"], p["ear"], checks.get("glowa_na_macie", False))

    noga_ok = checks.get("noga_w_gorze", False) and checks.get("noga_prosta", False)
    draw_segment(frame, raised["hip"], raised["knee"], noga_ok)
    draw_segment(frame, raised["knee"], raised["ankle"], noga_ok)

    draw_joint(frame, p["shoulder"],
               checks.get("linia_mostka", False) and checks.get("rece_przy_ciele", False) and checks.get(
                   "glowa_na_macie", False))
    draw_joint(frame, p["hip"], checks.get("linia_mostka", False))
    draw_joint(frame, p["knee"], checks.get("kolano_podporowe", False))
    draw_joint(frame, p["ankle"], checks.get("piszczel", False))
    draw_joint(frame, p["elbow"], checks.get("rece_przy_ciele", False))
    draw_joint(frame, p["wrist"], checks.get("rece_przy_ciele", False))
    draw_joint(frame, p["ear"], checks.get("glowa_na_macie", False))
    draw_joint(frame, raised["knee"], checks.get("noga_prosta", False))
    draw_joint(frame, raised["ankle"], noga_ok)


def process_side_view(frame, pose_model, check_phase, prev_raised_leg=None, skeleton_only=False):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose_model.process(rgb)
    output = frame.copy()
    if skeleton_only:
        output[:] = (0, 0, 0)

    if not results.pose_landmarks:
        cv2.putText(output, "Brak sylwetki", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2, cv2.LINE_AA)
        return output, False, {}

    h, w = output.shape[:2]
    p = get_side_points(results.pose_landmarks.landmark, w, h)

    checks, overall, metrics = detect_phase_side(p, check_phase, prev_raised_leg)

    if check_phase == 1:
        draw_phase1(output, p, checks)
        rows = [("Nogi ugiete", checks.get("nogi_ugiete", False)),
                ("Obie stopy na macie", checks.get("obie_stopy_na_ziemi", False)),
                ("Tulow lezy", checks.get("tulow_lezy", False)),
                ("Glowa na macie", checks.get("glowa_na_macie", False)),
                ("Rece przy ciele", checks.get("rece_przy_ciele", False))]
        title = "BOK: FAZA 1" if overall else "BOK: FAZA 1 - korekta"
    elif check_phase == 2:
        draw_phase2(output, p, checks)
        rows = [("Linia bark-biodro", checks.get("linia_mostka", False)), ("Kolano", checks.get("kolano", False)),
                ("Obie stopy na macie", checks.get("obie_stopy_na_ziemi", False)),
                ("Piszczel", checks.get("piszczel", False)), ("Glowa na macie", checks.get("glowa_na_macie", False)),
                ("Rece", checks.get("rece_przy_ciele", False))]
        title = "BOK: FAZA 2" if overall else "BOK: FAZA 2 - korekta"
    elif check_phase in (3, 4):
        draw_phase3(output, p, checks, metrics["raised"])
        rows = [
            ("Linia bark-biodro", checks.get("linia_mostka", False)),
            ("Kolano podporowe", checks.get("kolano_podporowe", False)),
            ("Piszczel", checks.get("piszczel", False)),
            ("Noga w gorze", checks.get("noga_w_gorze", False)),
            ("Noga prosta", checks.get("noga_prosta", False)),
            ("Glowa na macie", checks.get("glowa_na_macie", False))
        ]
        if check_phase == 4:
            rows.append(("Zmiana nogi", checks.get("zmiana_nogi", False)))
        title = f"BOK: FAZA {check_phase}" if overall else f"BOK: FAZA {check_phase} - korekta"
    else:
        rows = [("Zakonczono", True)]
        title = "BOK: ZAKONCZONO"

    extra = f"kolano={int(metrics['support_knee_angle']) if metrics['support_knee_angle'] is not None else -1}"
    output = draw_panel(output, title, rows, overall, extra)

    return output, overall, metrics


def process_front_view(frame, pose_model, check_phase, skeleton_only=False):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose_model.process(rgb)
    output = frame.copy()
    if skeleton_only:
        output[:] = (0, 0, 0)

    if not results.pose_landmarks:
        if check_phase == 1:
            output = draw_panel(output, "PRZOD: FAZA 1 - Kadr uciety", [("Brak sylwetki, polegam na boku", False)],
                                True, "")
            return output, True
        return output, False

    h, w = output.shape[:2]
    p = get_front_points(results.pose_landmarks.landmark, w, h)
    checks, metrics, overall = evaluate_front(p, check_phase)

    hips_ok = checks.get("biodra_sym", False)

    # Rysujemy tylko miednice i nogi
    draw_segment(output, p["l_hip"], p["r_hip"], hips_ok)
    for name in ["l_hip", "r_hip"]: draw_joint(output, p[name], hips_ok)

    if check_phase in (1, 2):
        draw_phase1_2_front(output, p, checks)
        rows = [("Biodra sym", checks.get("biodra_sym", False)), ("Kolana sym", checks.get("kolana_sym", False)),
                ("Kolana nad stopami", checks.get("kolana_nad_stopami", False))]

    elif check_phase == 3:  # Prawa noga
        prawa_ok = checks.get("prawa_noga_w_gorze", False)
        draw_segment(output, p["r_hip"], p["r_knee"], prawa_ok)
        draw_segment(output, p["r_knee"], p["r_ankle"], prawa_ok)
        draw_segment(output, p["l_hip"], p["l_knee"], True)  # Noga oparta jest zielona
        draw_segment(output, p["l_knee"], p["l_ankle"], True)
        for name in ["r_knee", "r_ankle"]: draw_joint(output, p[name], prawa_ok)
        for name in ["l_knee", "l_ankle"]: draw_joint(output, p[name], True)
        rows = [("Biodra sym", checks.get("biodra_sym", False)),
                ("PRAWA noga w gorze", checks.get("prawa_noga_w_gorze", False))]

    elif check_phase == 4:  # Lewa noga
        lewa_ok = checks.get("lewa_noga_w_gorze", False)
        draw_segment(output, p["l_hip"], p["l_knee"], lewa_ok)
        draw_segment(output, p["l_knee"], p["l_ankle"], lewa_ok)
        draw_segment(output, p["r_hip"], p["r_knee"], True)  # Noga oparta jest zielona
        draw_segment(output, p["r_knee"], p["r_ankle"], True)
        for name in ["l_knee", "l_ankle"]: draw_joint(output, p[name], lewa_ok)
        for name in ["r_knee", "r_ankle"]: draw_joint(output, p[name], True)
        rows = [("Biodra sym", checks.get("biodra_sym", False)),
                ("LEWA noga w gorze", checks.get("lewa_noga_w_gorze", False))]

    title = f"PRZOD: FAZA {check_phase}" if overall else f"PRZOD: FAZA {check_phase} - korekta"
    output = draw_panel(output, title, rows, overall, "")

    return output, overall


def main():
    cap_front = cv2.VideoCapture(CAMERA_FRONT_INDEX)
    cap_side = cv2.VideoCapture(CAMERA_SIDE_INDEX)

    if not cap_front.isOpened():
        print(f"Nie udalo sie otworzyc kamery FRONT: {CAMERA_FRONT_INDEX}")
        return
    if not cap_side.isOpened():
        print(f"Nie udalo sie otworzyc kamery SIDE: {CAMERA_SIDE_INDEX}")
        cap_front.release()
        return

    print("Sterowanie:")
    print("  ESC - wyjscie")
    print("  M   - przelacz obraz / sam szkielet")

    skeleton_only = SHOW_ONLY_SKELETON

    state = 1
    reps = 0

    frames_held = 0
    REQUIRED_FRAMES = 7
    prev_raised_leg = None

    while True:
        ok_front, frame_front = cap_front.read()
        ok_side, frame_side = cap_side.read()
        if not ok_front or not ok_side:
            print("Blad odczytu z jednej z kamer.")
            break

        frame_front = resize_to_height(frame_front, TARGET_HEIGHT)
        frame_side = resize_to_height(frame_side, TARGET_HEIGHT)

        check_phase = {1: 1, 2: 2, 3: 3, 4: 2, 5: 4}[state]

        view_side, ok_side_status, metrics = process_side_view(frame_side, pose_side, check_phase, prev_raised_leg,
                                                               skeleton_only=skeleton_only)
        view_front, ok_front_status = process_front_view(frame_front, pose_front, check_phase,
                                                         skeleton_only=skeleton_only)

        overall_ok = ok_side_status and ok_front_status

        if overall_ok:
            frames_held += 1
            if frames_held >= REQUIRED_FRAMES:
                if state == 3 and "raised" in metrics:
                    prev_raised_leg = metrics["raised"]["name"]

                state += 1

                if state > 5:
                    reps += 1
                    state = 1
                    prev_raised_leg = None

                frames_held = 0
        else:
            frames_held = max(0, frames_held - 1)

        combined = cv2.hconcat([view_side, view_front])

        cv2.putText(combined, f"POWTORZENIA: {reps}", (combined.shape[1] - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    YELLOW, 2, cv2.LINE_AA)

        if state == 1:
            msg = "PRZYGOTOWANIE: FAZA 1"
        elif state == 2:
            msg = "FAZA 2: UNIES BIODRA"
        elif state == 3:
            msg = "FAZA 3: PRAWA NOGA W GORE"
        elif state == 4:
            msg = "POWROT DO FAZY 2"
        elif state == 5:
            msg = "FAZA 4: LEWA NOGA W GORE"

        color = GREEN if overall_ok else RED
        cv2.putText(combined, msg, (20, combined.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3, cv2.LINE_AA)

        if frames_held > 0:
            bar_w = int(400 * (frames_held / REQUIRED_FRAMES))
            cv2.rectangle(combined, (20, combined.shape[0] - 20), (20 + bar_w, combined.shape[0] - 10), GREEN, -1)

        cv2.imshow(WINDOW_NAME, combined)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key in (ord('m'), ord('M')):
            skeleton_only = not skeleton_only

    cap_front.release()
    cap_side.release()
    pose_front.close()
    pose_side.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()