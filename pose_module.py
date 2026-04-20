import math
import cv2
import mediapipe as mp


CAMERA_FRONT_INDEX = 1
CAMERA_SIDE_INDEX = 0
TARGET_HEIGHT = 480
WINDOW_NAME = "Glute Bridge - Trener"
SHOW_ONLY_SKELETON = False

GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)

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
FRONT_PHASE34_KNEE_DIFF = 0

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


def close_pose_models():
    pose_front.close()
    pose_side.close()


def resize_to_height(frame, target_height=480):
    h, w = frame.shape[:2]
    new_width = int(w * target_height / h)
    return cv2.resize(frame, (new_width, target_height))


def to_px(lm, w, h):
    return int(lm.x * w), int(lm.y * h)


def midpoint(p1, p2):
    return ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)


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


def draw_joint(frame, point, ok, radius=7):
    color = GREEN if ok else RED
    cv2.circle(frame, point, radius, color, -1)
    cv2.circle(frame, point, radius + 2, WHITE, 1)


def draw_segment(frame, p1, p2, ok, thickness=5):
    color = GREEN if ok else RED
    cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)


def draw_panel(frame, title, status_rows, overall, extra_text=""):
    x0, y0 = 10, 10
    panel_w = 390
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
        cv2.putText(
            frame,
            extra_text,
            (x0 + 10, y0 + panel_h - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            WHITE,
            1,
            cv2.LINE_AA
        )
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
    sfx = "LEFT" if side == "LEFT" else "RIGHT"

    def p(name):
        return to_px(landmarks[getattr(ids, f"{sfx}_{name}").value], w, h)

    l_hip = to_px(landmarks[ids.LEFT_HIP.value], w, h)
    r_hip = to_px(landmarks[ids.RIGHT_HIP.value], w, h)
    l_knee = to_px(landmarks[ids.LEFT_KNEE.value], w, h)
    r_knee = to_px(landmarks[ids.RIGHT_KNEE.value], w, h)
    l_ankle = to_px(landmarks[ids.LEFT_ANKLE.value], w, h)
    r_ankle = to_px(landmarks[ids.RIGHT_ANKLE.value], w, h)

    return {
        "side": side,
        "ear": p("EAR"),
        "shoulder": p("SHOULDER"),
        "elbow": p("ELBOW"),
        "wrist": p("WRIST"),
        "hip": p("HIP"),
        "knee": p("KNEE"),
        "ankle": p("ANKLE"),
        "heel": p("HEEL"),
        "foot": p("FOOT_INDEX"),
        "l_hip": l_hip,
        "r_hip": r_hip,
        "l_knee": l_knee,
        "r_knee": r_knee,
        "l_ankle": l_ankle,
        "r_ankle": r_ankle,
        "hip_mid": midpoint(l_hip, r_hip),
        "shoulder_vis": landmarks[getattr(ids, f"{sfx}_SHOULDER").value].visibility,
        "l_hip_vis": landmarks[ids.LEFT_HIP.value].visibility,
        "r_hip_vis": landmarks[ids.RIGHT_HIP.value].visibility,
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
        "l_hip": to_px(landmarks[ids.LEFT_HIP.value], w, h),
        "r_hip": to_px(landmarks[ids.RIGHT_HIP.value], w, h),
        "l_knee": to_px(landmarks[ids.LEFT_KNEE.value], w, h),
        "r_knee": to_px(landmarks[ids.RIGHT_KNEE.value], w, h),
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
    ear = points["ear"]
    shoulder = points["shoulder"]
    elbow = points["elbow"]
    wrist = points["wrist"]
    hip = points["hip"]

    hip_ref = points["hip_mid"] if check_phase == 1 else hip

    support, raised = pick_support_and_raised(points)
    support_knee = support["knee"]
    support_ankle = support["ankle"]

    neck_angle = line_angle_deg(shoulder, ear)
    trunk_angle = line_angle_deg(shoulder, hip_ref)
    support_shin_angle = line_angle_deg(support_knee, support_ankle)
    support_knee_angle = angle(hip_ref, support_knee, support_ankle)
    arm_angle = angle(shoulder, elbow, wrist)
    hip_angle = angle(shoulder, hip_ref, support_knee)

    tulow_lezy = trunk_angle is not None and (trunk_angle <= 25 or trunk_angle >= 155)
    glowa_na_macie = neck_angle is not None and (neck_angle <= 40 or neck_angle >= 140)

    torso_len = dist(shoulder, hip_ref)
    biodra_nisko = abs(hip_ref[1] - shoulder[1]) <= max(20, int(torso_len * 0.22))

    hips_visible = max(points["l_hip_vis"], points["r_hip_vis"]) >= 0.55
    shoulder_visible = points["shoulder_vis"] >= 0.55
    phase1_landmarks_ok = hips_visible and shoulder_visible

    raised_leg_angle = angle(raised["hip"], raised["knee"], raised["ankle"])
    raised_leg_straight = raised_leg_angle is not None and raised_leg_angle >= STAGE34_RAISED_LEG_STRAIGHT_MIN

    raised_ankle_above_hip = hip[1] - raised["ankle"][1]
    raised_knee_above_hip = hip[1] - raised["knee"][1]

    raised_leg_up_soft = raised["ankle"][1] < hip[1] - 40
    raised_leg_up_strict = (
        raised_ankle_above_hip >= STAGE34_RAISED_ANKLE_ABOVE_HIP
        and raised_knee_above_hip >= STAGE34_RAISED_KNEE_ABOVE_HIP
    )

    is_bridge_stage2 = hip_angle is not None and hip_angle >= STAGE2_BRIDGE_MIN
    is_bridge_stage34 = hip_angle is not None and hip_angle >= STAGE34_BRIDGE_MIN
    hips_high_stage34 = hip_angle is not None and hip_angle >= STAGE34_HIP_HIGH_MIN

    stage1 = {
        "nogi_ugiete": support_knee_angle is not None and 50 <= support_knee_angle <= 145,
        "obie_stopy_na_ziemi": not raised_leg_up_soft,
        "tulow_lezy": tulow_lezy,
        "biodra_na_macie": biodra_nisko,
        "rece_przy_ciele": arm_angle is not None and arm_angle >= 145,
        "glowa_na_macie": glowa_na_macie,
    }

    stage2 = {
        "linia_mostka": is_bridge_stage2,
        "kolano": support_knee_angle is not None and 50 <= support_knee_angle <= 145,
        "piszczel": support_shin_angle is not None and 50 <= support_shin_angle <= 130,
        "obie_stopy_na_ziemi": not raised_leg_up_soft,
        "rece_przy_ciele": arm_angle is not None and arm_angle >= 145,
        "glowa_na_macie": glowa_na_macie,
    }

    stage3 = {
        "linia_mostka": is_bridge_stage34,
        "biodra_wysoko": hips_high_stage34,
        "kolano_podporowe": support_knee_angle is not None and STAGE34_SUPPORT_KNEE_MIN <= support_knee_angle <= STAGE34_SUPPORT_KNEE_MAX,
        "piszczel": support_shin_angle is not None and STAGE34_SUPPORT_SHIN_MIN <= support_shin_angle <= STAGE34_SUPPORT_SHIN_MAX,
        "noga_w_gorze": raised_leg_up_strict,
        "noga_prosta": raised_leg_straight,
        "rece_przy_ciele": arm_angle is not None and arm_angle >= 145,
        "glowa_na_macie": glowa_na_macie,
    }

    stage4 = {
        "linia_mostka": is_bridge_stage34,
        "biodra_wysoko": hips_high_stage34,
        "kolano_podporowe": support_knee_angle is not None and STAGE34_SUPPORT_KNEE_MIN <= support_knee_angle <= STAGE34_SUPPORT_KNEE_MAX,
        "piszczel": support_shin_angle is not None and STAGE34_SUPPORT_SHIN_MIN <= support_shin_angle <= STAGE34_SUPPORT_SHIN_MAX,
        "noga_w_gorze": raised_leg_up_strict,
        "noga_prosta": raised_leg_straight,
        "rece_przy_ciele": arm_angle is not None and arm_angle >= 145,
        "glowa_na_macie": glowa_na_macie,
        "zmiana_nogi": (raised["name"] != prev_raised_leg) if prev_raised_leg is not None else False
    }

    metrics = {
        "support": support,
        "raised": raised,
        "support_knee_angle": support_knee_angle,
        "hip_angle": hip_angle,
        "raised_ankle_above_hip": raised_ankle_above_hip,
        "raised_knee_above_hip": raised_knee_above_hip
    }

    if check_phase == 1:
        overall = all(stage1.values()) and phase1_landmarks_ok
        return stage1, overall, metrics
    elif check_phase == 2:
        return stage2, all(stage2.values()), metrics
    elif check_phase == 3:
        return stage3, all(stage3.values()), metrics
    elif check_phase == 4:
        return stage4, all(stage4.values()), metrics

    return {}, False, metrics


def evaluate_front(points, check_phase):
    hip_width = dist(points["l_hip"], points["r_hip"])
    knee_width = dist(points["l_knee"], points["r_knee"])
    ankle_width = dist(points["l_ankle"], points["r_ankle"])

    hip_level = abs(points["l_hip"][1] - points["r_hip"][1])
    knee_level = abs(points["l_knee"][1] - points["r_knee"][1])

    tol_h_phase12 = max(25, hip_width * FRONT_PHASE12_HIP_TOL_RATIO)
    tol_h_phase34 = max(FRONT_PHASE34_HIP_TOL_MIN, hip_width * FRONT_PHASE34_HIP_TOL_RATIO)

    tol_k = max(35, knee_width * 0.25 if knee_width > 0 else 35)
    tol_mid = max(40, ankle_width * 0.30 if ankle_width > 0 else 40)

    knee_over_ankle_l = abs(points["l_knee"][0] - points["l_ankle"][0])
    knee_over_ankle_r = abs(points["r_knee"][0] - points["r_ankle"][0])

    if check_phase in (1, 2):
        base = {"biodra_sym": hip_level <= tol_h_phase12}
        checks = {
            **base,
            "kolana_sym": knee_level <= tol_k,
            "kolana_nad_stopami": knee_over_ankle_l <= tol_mid and knee_over_ankle_r <= tol_mid
        }

    elif check_phase == 3:
        ankle_diff = points["l_ankle"][1] - points["r_ankle"][1]
        base = {"biodra_sym": hip_level <= tol_h_phase34}
        checks = {
            **base,
            "prawa_noga_w_gorze": ankle_diff >= FRONT_PHASE34_ANKLE_DIFF
        }

    elif check_phase == 4:
        ankle_diff = points["r_ankle"][1] - points["l_ankle"][1]
        base = {"biodra_sym": hip_level <= tol_h_phase34}
        checks = {
            **base,
            "lewa_noga_w_gorze": ankle_diff >= FRONT_PHASE34_ANKLE_DIFF
        }

    else:
        checks = {"biodra_sym": False}

    return checks, {"ratio": 0}, all(checks.values())


def draw_phase1_2_front(frame, p, checks):
    kolana_sym = checks.get("kolana_sym", True)
    kolana_nad_stopami = checks.get("kolana_nad_stopami", True)
    uda_ok = kolana_sym and kolana_nad_stopami

    draw_segment(frame, p["l_hip"], p["l_knee"], uda_ok)
    draw_segment(frame, p["r_hip"], p["r_knee"], uda_ok)
    draw_segment(frame, p["l_knee"], p["l_ankle"], kolana_nad_stopami)
    draw_segment(frame, p["r_knee"], p["r_ankle"], kolana_nad_stopami)

    for name in ["l_knee", "r_knee"]:
        draw_joint(frame, p[name], uda_ok)

    for name in ["l_ankle", "r_ankle"]:
        draw_joint(frame, p[name], kolana_nad_stopami)


def draw_side_skeleton(frame, p, checks, metrics, check_phase):
    mostek_ok = checks.get("linia_mostka", checks.get("tulow_lezy", True))
    biodra_wysoko_ok = checks.get("biodra_wysoko", True)
    trunk_ok = mostek_ok and biodra_wysoko_ok

    rece_ok = checks.get("rece_przy_ciele", True)
    kolano_ok = checks.get("kolano", checks.get("nogi_ugiete", True))
    glowa_ok = checks.get("glowa_na_macie", True)

    if check_phase in (3, 4):
        kolano_ok = checks.get("kolano_podporowe", True)

    piszczel_ok = checks.get("piszczel", True)

    draw_segment(frame, p["shoulder"], p["hip"], trunk_ok)
    draw_segment(frame, p["hip"], metrics["support"]["knee"], kolano_ok)
    draw_segment(frame, metrics["support"]["knee"], metrics["support"]["ankle"], piszczel_ok)
    draw_segment(frame, p["shoulder"], p["elbow"], rece_ok)
    draw_segment(frame, p["elbow"], p["wrist"], rece_ok)
    draw_segment(frame, p["shoulder"], p["ear"], glowa_ok)

    draw_joint(frame, p["shoulder"], trunk_ok and rece_ok and glowa_ok)
    draw_joint(frame, p["hip"], trunk_ok and kolano_ok)
    draw_joint(frame, metrics["support"]["knee"], kolano_ok)
    draw_joint(frame, metrics["support"]["ankle"], piszczel_ok)
    draw_joint(frame, p["elbow"], rece_ok)
    draw_joint(frame, p["wrist"], rece_ok)
    draw_joint(frame, p["ear"], glowa_ok)

    if check_phase in (3, 4):
        noga_prosta = checks.get("noga_prosta", False)
        noga_w_gorze = checks.get("noga_w_gorze", False)
        noga_ok = noga_prosta and noga_w_gorze

        draw_segment(frame, metrics["raised"]["hip"], metrics["raised"]["knee"], noga_ok)
        draw_segment(frame, metrics["raised"]["knee"], metrics["raised"]["ankle"], noga_ok)
        draw_joint(frame, metrics["raised"]["knee"], noga_ok)
        draw_joint(frame, metrics["raised"]["ankle"], noga_ok)


def process_side_view(frame, pose_model, check_phase, prev_raised_leg=None, skeleton_only=False):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose_model.process(rgb)
    output = frame.copy()

    if skeleton_only:
        output[:] = (0, 0, 0)

    if not results.pose_landmarks:
        cv2.putText(output, "Brak sylwetki", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2, cv2.LINE_AA)
        return output, False, {}, {}

    h, w = output.shape[:2]
    p = get_side_points(results.pose_landmarks.landmark, w, h)
    checks, overall, metrics = detect_phase_side(p, check_phase, prev_raised_leg)

    draw_side_skeleton(output, p, checks, metrics, check_phase)

    if check_phase in (3, 4):
        extra = (
            f"biodro={int(metrics['hip_angle']) if metrics['hip_angle'] is not None else -1}  "
            f"kol={int(metrics['support_knee_angle']) if metrics['support_knee_angle'] is not None else -1}  "
            f"stopa={int(metrics['raised_ankle_above_hip'])}"
        )
    else:
        extra = (
            f"biodro={int(metrics['hip_angle']) if metrics['hip_angle'] is not None else -1}  "
            f"kol={int(metrics['support_knee_angle']) if metrics['support_knee_angle'] is not None else -1}"
        )

    output = draw_panel(output, f"BOK: Oczekuje FAZA {check_phase}", checks.items(), overall, extra)
    return output, overall, metrics, checks


def process_front_view(frame, pose_model, check_phase, skeleton_only=False):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose_model.process(rgb)
    output = frame.copy()

    if skeleton_only:
        output[:] = (0, 0, 0)

    if not results.pose_landmarks:
        if check_phase == 1:
            output = draw_panel(output, "PRZOD: FAZA 1 - Kadr uciety", [("Brak sylwetki", False)], True, "")
            return output, True, {}
        return output, False, {}

    h, w = output.shape[:2]
    p = get_front_points(results.pose_landmarks.landmark, w, h)
    checks, metrics, overall = evaluate_front(p, check_phase)

    biodra_sym = checks.get("biodra_sym", False)
    draw_segment(output, p["l_hip"], p["r_hip"], biodra_sym)
    for name in ["l_hip", "r_hip"]:
        draw_joint(output, p[name], biodra_sym)

    if check_phase in (1, 2):
        draw_phase1_2_front(output, p, checks)
    elif check_phase == 3:
        prawa_ok = checks.get("prawa_noga_w_gorze", False)
        draw_segment(output, p["r_hip"], p["r_knee"], prawa_ok)
        draw_segment(output, p["r_knee"], p["r_ankle"], prawa_ok)
        for name in ["r_knee", "r_ankle"]:
            draw_joint(output, p[name], prawa_ok)
    elif check_phase == 4:
        lewa_ok = checks.get("lewa_noga_w_gorze", False)
        draw_segment(output, p["l_hip"], p["l_knee"], lewa_ok)
        draw_segment(output, p["l_knee"], p["l_ankle"], lewa_ok)
        for name in ["l_knee", "l_ankle"]:
            draw_joint(output, p[name], lewa_ok)

    output = draw_panel(output, f"PRZOD: Oczekuje FAZA {check_phase}", checks.items(), overall, "")
    return output, overall, checks