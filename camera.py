import math
import cv2
import mediapipe as mp

CAMERA_FRONT_INDEX = 0
CAMERA_SIDE_INDEX = 1
TARGET_HEIGHT = 480
WINDOW_NAME = "Glute Bridge - fazy 1/2/3"
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
        cv2.putText(frame, extra_text, (x0 + 10, y0 + panel_h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1, cv2.LINE_AA)
    return frame


def visible_side_name(landmarks):
    ids = mp_pose.PoseLandmark
    left_vis = (
        landmarks[ids.LEFT_SHOULDER.value].visibility
        + landmarks[ids.LEFT_HIP.value].visibility
        + landmarks[ids.LEFT_KNEE.value].visibility
    )
    right_vis = (
        landmarks[ids.RIGHT_SHOULDER.value].visibility
        + landmarks[ids.RIGHT_HIP.value].visibility
        + landmarks[ids.RIGHT_KNEE.value].visibility
    )
    return "LEFT" if left_vis >= right_vis else "RIGHT"


def get_side_points(landmarks, w, h):
    ids = mp_pose.PoseLandmark
    side = visible_side_name(landmarks)
    if side == "LEFT":
        sfx = "LEFT"
    else:
        sfx = "RIGHT"

    def p(name):
        idx = getattr(ids, f"{sfx}_{name}").value
        return to_px(landmarks[idx], w, h)

    points = {
        "side": side,
        "shoulder": p("SHOULDER"),
        "elbow": p("ELBOW"),
        "wrist": p("WRIST"),
        "hip": p("HIP"),
        "knee": p("KNEE"),
        "ankle": p("ANKLE"),
        "heel": p("HEEL"),
        "foot": p("FOOT_INDEX"),
        "l_hip": to_px(landmarks[ids.LEFT_HIP.value], w, h),
        "r_hip": to_px(landmarks[ids.RIGHT_HIP.value], w, h),
        "l_knee": to_px(landmarks[ids.LEFT_KNEE.value], w, h),
        "r_knee": to_px(landmarks[ids.RIGHT_KNEE.value], w, h),
        "l_ankle": to_px(landmarks[ids.LEFT_ANKLE.value], w, h),
        "r_ankle": to_px(landmarks[ids.RIGHT_ANKLE.value], w, h),
        "l_foot": to_px(landmarks[ids.LEFT_FOOT_INDEX.value], w, h),
        "r_foot": to_px(landmarks[ids.RIGHT_FOOT_INDEX.value], w, h),
        "l_heel": to_px(landmarks[ids.LEFT_HEEL.value], w, h),
        "r_heel": to_px(landmarks[ids.RIGHT_HEEL.value], w, h),
    }
    return points


def get_front_points(landmarks, w, h):
    ids = mp_pose.PoseLandmark
    return {
        "l_shoulder": to_px(landmarks[ids.LEFT_SHOULDER.value], w, h),
        "r_shoulder": to_px(landmarks[ids.RIGHT_SHOULDER.value], w, h),
        "l_elbow": to_px(landmarks[ids.LEFT_ELBOW.value], w, h),
        "r_elbow": to_px(landmarks[ids.RIGHT_ELBOW.value], w, h),
        "l_wrist": to_px(landmarks[ids.LEFT_WRIST.value], w, h),
        "r_wrist": to_px(landmarks[ids.RIGHT_WRIST.value], w, h),
        "l_hip": to_px(landmarks[ids.LEFT_HIP.value], w, h),
        "r_hip": to_px(landmarks[ids.RIGHT_HIP.value], w, h),
        "l_knee": to_px(landmarks[ids.LEFT_KNEE.value], w, h),
        "r_knee": to_px(landmarks[ids.RIGHT_KNEE.value], w, h),
        "l_ankle": to_px(landmarks[ids.LEFT_ANKLE.value], w, h),
        "r_ankle": to_px(landmarks[ids.RIGHT_ANKLE.value], w, h),
    }


def pick_support_and_raised(points):
    legs = [
        {
            "name": "left",
            "hip": points["l_hip"],
            "knee": points["l_knee"],
            "ankle": points["l_ankle"],
            "foot": points["l_foot"],
            "heel": points["l_heel"],
        },
        {
            "name": "right",
            "hip": points["r_hip"],
            "knee": points["r_knee"],
            "ankle": points["r_ankle"],
            "foot": points["r_foot"],
            "heel": points["r_heel"],
        },
    ]
    support = max(legs, key=lambda leg: leg["ankle"][1])
    raised = legs[0] if support["name"] == "right" else legs[1]
    return support, raised


def detect_phase_side(points):
    shoulder = points["shoulder"]
    elbow = points["elbow"]
    wrist = points["wrist"]
    hip = points["hip"]
    support, raised = pick_support_and_raised(points)

    support_knee = support["knee"]
    support_ankle = support["ankle"]
    support_foot = support["foot"]

    trunk_angle = line_angle_deg(shoulder, hip)
    support_thigh_angle = line_angle_deg(hip, support_knee)
    support_shin_angle = line_angle_deg(support_knee, support_ankle)
    support_knee_angle = angle(hip, support_knee, support_ankle)
    arm_angle = angle(shoulder, elbow, wrist)

    hip_to_line = point_line_distance(hip, shoulder, support_knee)
    foot_len = max(1.0, dist(support_ankle, support_foot))

    raised_leg_up = raised["ankle"][1] < hip[1] - 40
    raised_leg_straight = False
    raised_leg_angle = angle(raised["hip"], raised["knee"], raised["ankle"])
    if raised_leg_angle is not None:
        raised_leg_straight = raised_leg_angle >= 155

    stage1 = {
        "nogi_ugiete": support_knee_angle is not None and 70 <= support_knee_angle <= 125,
        "biodra_nisko": hip_to_line >= max(18, foot_len * 1.8),
        "rece_przy_ciele": arm_angle is not None and arm_angle >= 145,
    }

    stage2 = {
        "linia_mostka": trunk_angle is not None and support_thigh_angle is not None and abs(trunk_angle - support_thigh_angle) <= 20,
        "kolano": support_knee_angle is not None and 70 <= support_knee_angle <= 120,
        "piszczel": support_shin_angle is not None and 65 <= support_shin_angle <= 115,
        "rece_przy_ciele": arm_angle is not None and arm_angle >= 145,
    }

    stage3 = {
        "linia_mostka": stage2["linia_mostka"],
        "kolano_podporowe": stage2["kolano"],
        "piszczel": stage2["piszczel"],
        "noga_w_gorze": raised_leg_up,
        "noga_prosta": raised_leg_straight,
        "rece_przy_ciele": stage2["rece_przy_ciele"],
    }

    score1 = sum(stage1.values())
    score2 = sum(stage2.values())
    score3 = sum(stage3.values())

    if stage3["noga_w_gorze"] and score3 >= 5:
        phase = 3
        checks = stage3
        ok = all(stage3.values())
    elif score2 >= 3 and not stage3["noga_w_gorze"]:
        phase = 2
        checks = stage2
        ok = all(stage2.values())
    elif score1 >= 2:
        phase = 1
        checks = stage1
        ok = all(stage1.values())
    else:
        phase = 0
        checks = stage2
        ok = False

metrics = {
        "support_knee_angle": support_knee_angle,
        "trunk_angle": trunk_angle,
        "support_thigh_angle": support_thigh_angle,
        "raised_leg_angle": raised_leg_angle,
        "hip_to_line": hip_to_line,
        "support": support,
        "raised": raised,
    }
    return phase, checks, ok, metrics


def evaluate_front(points, phase):
    hip_width = dist(points["l_hip"], points["r_hip"])
    knee_width = dist(points["l_knee"], points["r_knee"])
    ankle_width = dist(points["l_ankle"], points["r_ankle"])
    shoulder_width = dist(points["l_shoulder"], points["r_shoulder"])

    hip_level = abs(points["l_hip"][1] - points["r_hip"][1])
    knee_level = abs(points["l_knee"][1] - points["r_knee"][1])
    ankle_level = abs(points["l_ankle"][1] - points["r_ankle"][1])
    wrist_level = abs(points["l_wrist"][1] - points["r_wrist"][1])

    tol_h = max(15, hip_width * 0.12)
    tol_k = max(15, knee_width * 0.12 if knee_width > 0 else 15)
    tol_a = max(15, ankle_width * 0.12 if ankle_width > 0 else 15)
    tol_w = max(20, shoulder_width * 0.18)

    knee_over_ankle_l = abs(points["l_knee"][0] - points["l_ankle"][0])
    knee_over_ankle_r = abs(points["r_knee"][0] - points["r_ankle"][0])
    tol_mid = max(25, ankle_width * 0.18 if ankle_width > 0 else 25)

    ratio = knee_width / ankle_width if ankle_width > 1 else 0
    arms_span_diff = abs(dist(points["l_shoulder"], points["l_wrist"]) - dist(points["r_shoulder"], points["r_wrist"]))

    base = {
        "biodra_sym": hip_level <= tol_h,
        "rece_sym": wrist_level <= tol_w and arms_span_diff <= max(20, shoulder_width * 0.2),
    }

    if phase in (1, 2):
        checks = {
            **base,
            "kolana_sym": knee_level <= tol_k,
            "kostki_sym": ankle_level <= tol_a,
            "kolana_nad_stopami": knee_over_ankle_l <= tol_mid and knee_over_ankle_r <= tol_mid and 0.7 <= ratio <= 1.3,
        }
    else:
        checks = {
            **base,
            "stabilny_tulow": hip_level <= tol_h,
        }

    metrics = {"ratio": ratio}
    return checks, metrics, all(checks.values())


def draw_phase1(frame, p, checks):
    draw_segment(frame, p["shoulder"], p["hip"], checks["biodra_nisko"])
    draw_segment(frame, p["hip"], p["knee"], checks["nogi_ugiete"])
    draw_segment(frame, p["knee"], p["ankle"], checks["nogi_ugiete"])
    draw_segment(frame, p["shoulder"], p["elbow"], checks["rece_przy_ciele"])
    draw_segment(frame, p["elbow"], p["wrist"], checks["rece_przy_ciele"])

    draw_joint(frame, p["shoulder"], checks["biodra_nisko"] and checks["rece_przy_ciele"])
    draw_joint(frame, p["hip"], checks["biodra_nisko"])
    draw_joint(frame, p["knee"], checks["nogi_ugiete"])
    draw_joint(frame, p["ankle"], checks["nogi_ugiete"])
    draw_joint(frame, p["elbow"], checks["rece_przy_ciele"])
    draw_joint(frame, p["wrist"], checks["rece_przy_ciele"])


def draw_phase2(frame, p, checks):
    draw_segment(frame, p["shoulder"], p["hip"], checks["linia_mostka"])
    draw_segment(frame, p["hip"], p["knee"], checks["linia_mostka"])
    draw_segment(frame, p["knee"], p["ankle"], checks["piszczel"])
    draw_segment(frame, p["shoulder"], p["elbow"], checks["rece_przy_ciele"])
    draw_segment(frame, p["elbow"], p["wrist"], checks["rece_przy_ciele"])

    draw_joint(frame, p["shoulder"], checks["linia_mostka"] and checks["rece_przy_ciele"])
    draw_joint(frame, p["hip"], checks["linia_mostka"])
    draw_joint(frame, p["knee"], checks["kolano"])
    draw_joint(frame, p["ankle"], checks["piszczel"])
    draw_joint(frame, p["elbow"], checks["rece_przy_ciele"])
    draw_joint(frame, p["wrist"], checks["rece_przy_ciele"])


def draw_phase3(frame, p, checks, raised):
    draw_segment(frame, p["shoulder"], p["hip"], checks["linia_mostka"])
    draw_segment(frame, p["hip"], p["knee"], checks["linia_mostka"])
    draw_segment(frame, p["knee"], p["ankle"], checks["piszczel"])
    draw_segment(frame, p["shoulder"], p["elbow"], checks["rece_przy_ciele"])
    draw_segment(frame, p["elbow"], p["wrist"], checks["rece_przy_ciele"])
    draw_segment(frame, raised["hip"], raised["knee"], checks["noga_w_gorze"] and checks["noga_prosta"])
    draw_segment(frame, raised["knee"], raised["ankle"], checks["noga_w_gorze"] and checks["noga_prosta"])

    draw_joint(frame, p["shoulder"], checks["linia_mostka"] and checks["rece_przy_ciele"])
    draw_joint(frame, p["hip"], checks["linia_mostka"])
    draw_joint(frame, p["knee"], checks["kolano_podporowe"])
    draw_joint(frame, p["ankle"], checks["piszczel"])
    draw_joint(frame, p["elbow"], checks["rece_przy_ciele"])
    draw_joint(frame, p["wrist"], checks["rece_przy_ciele"])
    draw_joint(frame, raised["knee"], checks["noga_prosta"])
    draw_joint(frame, raised["ankle"], checks["noga_w_gorze"] and checks["noga_prosta"])


def process_side_view(frame, pose_model, skeleton_only=False):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose_model.process(rgb)
    output = frame.copy()
    if skeleton_only:
        output[:] = (0, 0, 0)

    if not results.pose_landmarks:
        cv2.putText(output, "Brak sylwetki", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2, cv2.LINE_AA)
        return output, 0, False

    h, w = output.shape[:2]
    p = get_side_points(results.pose_landmarks.landmark, w, h)
    phase, checks, overall, metrics = detect_phase_side(p)

    if phase == 1:
        draw_phase1(output, p, checks)
        rows = [("Nogi ugiete", checks["nogi_ugiete"]), ("Biodra nisko", checks["biodra_nisko"]), ("Rece przy ciele", checks["rece_przy_ciele"])]
        title = "BOK: ETAP 1" if overall else "BOK: ETAP 1 - korekta"
    elif phase == 2:
        draw_phase2(output, p, checks)
        rows = [("Linia bark-biodro-kolano", checks["linia_mostka"]), ("Kolano", checks["kolano"]), ("Piszczel", checks["piszczel"]), ("Rece przy ciele", checks["rece_przy_ciele"])]
        title = "BOK: ETAP 2" if overall else "BOK: ETAP 2 - korekta"
    elif phase == 3:
        draw_phase3(output, p, checks, metrics["raised"])
        rows = [("Linia bark-biodro-kolano", checks["linia_mostka"]), ("Kolano podporowe", checks["kolano_podporowe"]), ("Piszczel", checks["piszczel"]), ("Noga w gorze", checks["noga_w_gorze"]), ("Noga prosta", checks["noga_prosta"]), ("Rece przy ciele", checks["rece_przy_ciele"])]
        title = "BOK: ETAP 3" if overall else "BOK: ETAP 3 - korekta"
    else:
        draw_phase2(output, p, checks)
        rows = [("Poza poprawna faza", False)]
        title = "BOK: nieczytelna poza"

    extra = f"kolano={int(metrics['support_knee_angle']) if metrics['support_knee_angle'] is not None else -1}"
    output = draw_panel(output, title, rows, overall, extra)
    cv2.putText(output, "Widok boczny - fazy", (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2, cv2.LINE_AA)
    return output, phase, overall


def process_front_view(frame, pose_model, phase, skeleton_only=False):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose_model.process(rgb)
    output = frame.copy()
    if skeleton_only:
        output[:] = (0, 0, 0)

    if not results.pose_landmarks:
        cv2.putText(output, "Brak sylwetki", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2, cv2.LINE_AA)
        return output, False

    h, w = output.shape[:2]
    p = get_front_points(results.pose_landmarks.landmark, w, h)
    checks, metrics, overall = evaluate_front(p, phase)

    arms_ok = checks["rece_sym"]
    hips_ok = checks["biodra_sym"]
    knees_ok = checks.get("kolana_sym", True) and checks.get("kolana_nad_stopami", True)
    ankles_ok = checks.get("kostki_sym", True) and checks.get("kolana_nad_stopami", True)

    draw_segment(output, p["l_shoulder"], p["l_elbow"], arms_ok)
    draw_segment(output, p["l_elbow"], p["l_wrist"], arms_ok)
    draw_segment(output, p["r_shoulder"], p["r_elbow"], arms_ok)
    draw_segment(output, p["r_elbow"], p["r_wrist"], arms_ok)
    draw_segment(output, p["l_shoulder"], p["l_hip"], hips_ok)
    draw_segment(output, p["r_shoulder"], p["r_hip"], hips_ok)
    draw_segment(output, p["l_hip"], p["r_hip"], hips_ok)
    draw_segment(output, p["l_hip"], p["l_knee"], knees_ok)
    draw_segment(output, p["r_hip"], p["r_knee"], knees_ok)
    draw_segment(output, p["l_knee"], p["l_ankle"], ankles_ok)
    draw_segment(output, p["r_knee"], p["r_ankle"], ankles_ok)

    for name in ["l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist"]:
        draw_joint(output, p[name], arms_ok)
    for name in ["l_hip", "r_hip"]:
        draw_joint(output, p[name], hips_ok)
    for name in ["l_knee", "r_knee"]:
        draw_joint(output, p[name], knees_ok)
    for name in ["l_ankle", "r_ankle"]:
        draw_joint(output, p[name], ankles_ok)

    if phase in (1, 2):
        rows = [("Biodra sym", checks["biodra_sym"]), ("Kolana sym", checks["kolana_sym"]), ("Kolana nad stopami", checks["kolana_nad_stopami"]), ("Kostki sym", checks["kostki_sym"]), ("Rece sym", checks["rece_sym"])]
    else:
        rows = [("Biodra sym", checks["biodra_sym"]), ("Tulow stabilny", checks["stabilny_tulow"]), ("Rece sym", checks["rece_sym"])]

    title = f"PRZOD: ETAP {phase}" if phase in (1, 2, 3) else "PRZOD: podglad"
    ratio_txt = f"kolana/stopy={metrics['ratio']:.2f}" if 'ratio' in metrics else ""
    output = draw_panel(output, title, rows, overall, ratio_txt)
    cv2.putText(output, "Widok z przodu", (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2, cv2.LINE_AA)
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

    while True:
        ok_front, frame_front = cap_front.read()
        ok_side, frame_side = cap_side.read()
        if not ok_front or not ok_side:
            print("Blad odczytu z jednej z kamer.")
            break

        frame_front = resize_to_height(frame_front, TARGET_HEIGHT)
        frame_side = resize_to_height(frame_side, TARGET_HEIGHT)

        view_side, phase, ok_side_phase = process_side_view(frame_side, pose_side, skeleton_only=skeleton_only)
        view_front, ok_front_phase = process_front_view(frame_front, pose_front, phase, skeleton_only=skeleton_only)

        combined = cv2.hconcat([view_side, view_front])
        if phase == 0:
            msg = "USTAW SIE DO ETAPU 1, 2 LUB 3"
            color = RED
        else:
            overall_ok = ok_side_phase and ok_front_phase
            msg = f"ETAP {phase} POPRAWNY" if overall_ok else f"ETAP {phase} - SKORYGUJ ULOZENIE"
            color = GREEN if overall_ok else RED
        cv2.putText(combined, msg, (20, combined.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3, cv2.LINE_AA)

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


if _name_ == "_main_":
    main()