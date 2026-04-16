import math
import cv2
import mediapipe as mp

CAMERA_FRONT_INDEX = 0
CAMERA_SIDE_INDEX = 1
TARGET_HEIGHT = 480
WINDOW_NAME = "Glute Bridge - dual feedback"
SHOW_ONLY_SKELETON = False

GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

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


def draw_joint(frame, point, ok, radius=7):
    color = GREEN if ok else RED
    cv2.circle(frame, point, radius, color, -1)
    cv2.circle(frame, point, radius + 2, WHITE, 1)


def draw_segment(frame, p1, p2, ok, thickness=5):
    color = GREEN if ok else RED
    cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)


def draw_panel(frame, title, status_rows, overall, extra_text=""):
    x0, y0 = 10, 10
    panel_w = 320
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


def get_side_points(landmarks, w, h):
    ids = mp_pose.PoseLandmark
    return {
        "shoulder": to_px(landmarks[ids.LEFT_SHOULDER.value], w, h),
        "elbow": to_px(landmarks[ids.LEFT_ELBOW.value], w, h),
        "wrist": to_px(landmarks[ids.LEFT_WRIST.value], w, h),
        "hip": to_px(landmarks[ids.LEFT_HIP.value], w, h),
        "knee": to_px(landmarks[ids.LEFT_KNEE.value], w, h),
        "ankle": to_px(landmarks[ids.LEFT_ANKLE.value], w, h),
        "ear": to_px(landmarks[ids.LEFT_EAR.value], w, h),
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


def evaluate_side(points):
    shoulder = points["shoulder"]
    elbow = points["elbow"]
    wrist = points["wrist"]
    hip = points["hip"]
    knee = points["knee"]
    ankle = points["ankle"]
    ear = points["ear"]

    trunk_angle = line_angle_deg(shoulder, hip)
    thigh_angle = line_angle_deg(hip, knee)
    shin_angle = line_angle_deg(knee, ankle)
    arm_angle = angle(shoulder, elbow, wrist)
    knee_angle = angle(hip, knee, ankle)
    neck_angle = line_angle_deg(shoulder, ear)

    checks = {
        "hips": abs(trunk_angle - thigh_angle) <= 20 if trunk_angle is not None and thigh_angle is not None else False,
        "knee_bent": 70 <= knee_angle <= 120 if knee_angle is not None else False,
        "foot_base": 65 <= shin_angle <= 115 if shin_angle is not None else False,
        "arms": arm_angle >= 150 if arm_angle is not None else False,
        "neck": neck_angle <= 35 if neck_angle is not None else False,
    }
    metrics = {
        "knee_angle": knee_angle,
        "trunk_angle": trunk_angle,
        "thigh_angle": thigh_angle,
    }
    return checks, metrics, all(checks.values())


def evaluate_front(points):
    l_shoulder, r_shoulder = points["l_shoulder"], points["r_shoulder"]
    l_elbow, r_elbow = points["l_elbow"], points["r_elbow"]
    l_wrist, r_wrist = points["l_wrist"], points["r_wrist"]
    l_hip, r_hip = points["l_hip"], points["r_hip"]
    l_knee, r_knee = points["l_knee"], points["r_knee"]
    l_ankle, r_ankle = points["l_ankle"], points["r_ankle"]

    hip_width = dist(l_hip, r_hip)
    knee_width = dist(l_knee, r_knee)
    ankle_width = dist(l_ankle, r_ankle)
    shoulder_width = dist(l_shoulder, r_shoulder)

    hip_level = abs(l_hip[1] - r_hip[1])
    knee_level = abs(l_knee[1] - r_knee[1])
    ankle_level = abs(l_ankle[1] - r_ankle[1])
    wrist_level = abs(l_wrist[1] - r_wrist[1])

    tol_h = max(15, hip_width * 0.12)
    tol_k = max(15, knee_width * 0.12 if knee_width > 0 else 15)
    tol_a = max(15, ankle_width * 0.12 if ankle_width > 0 else 15)
    tol_w = max(20, shoulder_width * 0.18)

    knee_over_ankle_l = abs(l_knee[0] - l_ankle[0])
    knee_over_ankle_r = abs(r_knee[0] - r_ankle[0])
    tol_mid = max(25, ankle_width * 0.18 if ankle_width > 0 else 25)

    ratio = knee_width / ankle_width if ankle_width > 1 else 0
    arms_span_diff = abs(dist(l_shoulder, l_wrist) - dist(r_shoulder, r_wrist))

    checks = {
        "hips_symmetry": hip_level <= tol_h,
        "knees_symmetry": knee_level <= tol_k,
        "ankles_symmetry": ankle_level <= tol_a,
        "knees_alignment": knee_over_ankle_l <= tol_mid and knee_over_ankle_r <= tol_mid and 0.7 <= ratio <= 1.3,
        "arms_symmetry": wrist_level <= tol_w and arms_span_diff <= max(20, shoulder_width * 0.2),
    }
    metrics = {
        "hip_level": hip_level,
        "knee_level": knee_level,
        "ankle_level": ankle_level,
        "ratio": ratio,
    }
    return checks, metrics, all(checks.values())


def process_side_view(frame, pose_model, skeleton_only=False):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose_model.process(rgb)
    output = frame.copy()
    if skeleton_only:
        output[:] = (0, 0, 0)

    if not results.pose_landmarks:
        cv2.putText(output, "Brak sylwetki", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2, cv2.LINE_AA)
        return output, False

    h, w = output.shape[:2]
    p = get_side_points(results.pose_landmarks.landmark, w, h)
    checks, metrics, overall = evaluate_side(p)

    draw_segment(output, p["shoulder"], p["hip"], checks["hips"])
    draw_segment(output, p["hip"], p["knee"], checks["hips"])
    draw_segment(output, p["knee"], p["ankle"], checks["foot_base"])
    draw_segment(output, p["shoulder"], p["elbow"], checks["arms"])
    draw_segment(output, p["elbow"], p["wrist"], checks["arms"])
    draw_segment(output, p["shoulder"], p["ear"], checks["neck"])

    draw_joint(output, p["shoulder"], checks["hips"] and checks["arms"] and checks["neck"])
    draw_joint(output, p["hip"], checks["hips"])
    draw_joint(output, p["knee"], checks["hips"] and checks["knee_bent"] and checks["foot_base"])
    draw_joint(output, p["ankle"], checks["foot_base"])
    draw_joint(output, p["elbow"], checks["arms"])
    draw_joint(output, p["wrist"], checks["arms"])
    draw_joint(output, p["ear"], checks["neck"])

    rows = [
        ("Biodra", checks["hips"]),
        ("Kolano", checks["knee_bent"]),
        ("Stopa / piszczel", checks["foot_base"]),
        ("Rece", checks["arms"]),
        ("Szyja", checks["neck"]),
    ]
    knee_text = f"kolano={int(metrics['knee_angle']) if metrics['knee_angle'] is not None else -1}"
    output = draw_panel(output, "BOK: OK" if overall else "BOK: KOREKTA", rows, overall, knee_text)
    cv2.putText(output, "Widok boczny", (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2, cv2.LINE_AA)
    return output, overall


def process_front_view(frame, pose_model, skeleton_only=False):
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
    checks, metrics, overall = evaluate_front(p)

    hips_ok = checks["hips_symmetry"]
    knees_ok = checks["knees_symmetry"] and checks["knees_alignment"]
    ankles_ok = checks["ankles_symmetry"] and checks["knees_alignment"]
    arms_ok = checks["arms_symmetry"]

    draw_segment(output, p["l_shoulder"], p["l_elbow"], arms_ok)
    draw_segment(output, p["l_elbow"], p["l_wrist"], arms_ok)
    draw_segment(output, p["r_shoulder"], p["r_elbow"], arms_ok)
    draw_segment(output, p["r_elbow"], p["r_wrist"], arms_ok)
    draw_segment(output, p["l_shoulder"], p["l_hip"], hips_ok)
    draw_segment(output, p["r_shoulder"], p["r_hip"], hips_ok)
    draw_segment(output, p["l_hip"], p["l_knee"], knees_ok)
    draw_segment(output, p["r_hip"], p["r_knee"], knees_ok)
    draw_segment(output, p["l_knee"], p["l_ankle"], ankles_ok)
    draw_segment(output, p["r_knee"], p["r_ankle"], ankles_ok)
    draw_segment(output, p["l_shoulder"], p["r_shoulder"], hips_ok)
    draw_segment(output, p["l_hip"], p["r_hip"], hips_ok)

    for name in ["l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist"]:
        draw_joint(output, p[name], arms_ok)
    for name in ["l_hip", "r_hip"]:
        draw_joint(output, p[name], hips_ok)
    for name in ["l_knee", "r_knee"]:
        draw_joint(output, p[name], knees_ok)
    for name in ["l_ankle", "r_ankle"]:
        draw_joint(output, p[name], ankles_ok)

    rows = [
        ("Biodra symetria", checks["hips_symmetry"]),
        ("Kolana symetria", checks["knees_symmetry"]),
        ("Kolana nad stopami", checks["knees_alignment"]),
        ("Kostki / stopy", checks["ankles_symmetry"]),
        ("Rece symetria", checks["arms_symmetry"]),
    ]
    ratio_txt = f"kolana/stopy={metrics['ratio']:.2f}" if metrics['ratio'] else "kolana/stopy=0.00"
    output = draw_panel(output, "PRZOD: OK" if overall else "PRZOD: KOREKTA", rows, overall, ratio_txt)
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

        view_side, ok_side_pose = process_side_view(frame_side, pose_side, skeleton_only=skeleton_only)
        view_front, ok_front_pose = process_front_view(frame_front, pose_front, skeleton_only=skeleton_only)

        combined = cv2.hconcat([view_side, view_front])
        overall_ok = ok_side_pose and ok_front_pose
        txt = "CWICZENIE POPRAWNE" if overall_ok else "SKORYGUJ ULOZENIE"
        color = GREEN if overall_ok else RED
        cv2.putText(combined, txt, (20, combined.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3, cv2.LINE_AA)

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