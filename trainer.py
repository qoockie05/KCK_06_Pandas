import cv2
import numpy as np
import random

from voice_assistant import VoiceAssistant
from pose_module import (
    CAMERA_FRONT_INDEX,
    CAMERA_SIDE_INDEX,
    TARGET_HEIGHT,
    WINDOW_NAME,
    SHOW_ONLY_SKELETON,
    RED,
    GREEN,
    YELLOW,
    ERROR_MESSAGES_SIDE,
    ERROR_MESSAGES_FRONT,
    pose_front,
    pose_side,
    close_pose_models,
    resize_to_height,
    process_side_view,
    process_front_view,
)


def main():
    assistant = VoiceAssistant()

    cap_front = cv2.VideoCapture(CAMERA_FRONT_INDEX)
    cap_side = cv2.VideoCapture(CAMERA_SIDE_INDEX)

    if not cap_side.isOpened():
        print(f"Nie udalo sie otworzyc GŁÓWNEJ kamery z boku (indeks {CAMERA_SIDE_INDEX}).")
        return

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("Sterowanie:")
    print("  ESC - wyjscie")
    print("  M   - przelacz obraz / sam szkielet")
    print("  N   - wymuś koniec treningu")

    skeleton_only = SHOW_ONLY_SKELETON

    state = 1
    reps = 0
    frames_held = 0

    REQUIRED_FRAMES_PHASE1 = 15
    REQUIRED_FRAMES = 7
    prev_raised_leg = None

    consecutive_errors = 0
    error_cooldown = 0
    ERROR_THRESHOLD = 40
    COOLDOWN_FRAMES = 150

    assistant.speak("Cześć, zaczynajmy. Połóż się na macie i przygotuj do ćwiczenia.")

    while True:
        assistant.listen_active = (state == 1)

        if assistant.stop_requested:
            assistant.speak("Kończymy na dzisiaj. Dziękuję za wspólny trening, świetna robota!")
            print("\nZakończono trening. Odpowiedź użytkownika: STOP/KONIEC.")
            cv2.waitKey(4000)
            break

        ok_side, frame_side = cap_side.read()
        if not ok_side:
            cv2.waitKey(10)
            continue

        ok_front, frame_front = cap_front.read()
        if ok_front:
            frame_front = cv2.rotate(frame_front, cv2.ROTATE_90_CLOCKWISE)
            frame_front = resize_to_height(frame_front, TARGET_HEIGHT)
        else:
            frame_front = np.zeros((TARGET_HEIGHT, 640, 3), dtype=np.uint8)
            cv2.putText(
                frame_front,
                "BRAK KAMERY PRZOD",
                (140, int(TARGET_HEIGHT / 2)),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                RED,
                3,
                cv2.LINE_AA
            )

        frame_side = resize_to_height(frame_side, TARGET_HEIGHT)

        check_phase = state

        view_side, ok_side_status, metrics, checks_side = process_side_view(
            frame_side, pose_side, check_phase, prev_raised_leg, skeleton_only=skeleton_only
        )

        if ok_front:
            view_front, ok_front_status, checks_front = process_front_view(
                frame_front, pose_front, check_phase, skeleton_only=skeleton_only
            )
        else:
            view_front = frame_front
            ok_front_status = True
            checks_front = {}

        overall_ok = ok_side_status and ok_front_status
        current_required = REQUIRED_FRAMES_PHASE1 if state == 1 else REQUIRED_FRAMES

        if overall_ok:
            frames_held += 1
            consecutive_errors = 0

            if frames_held >= current_required:
                if state == 1:
                    msg = random.choice([
                        "Okej, teraz podnieś biodra.",
                        "Świetnie, wypchnij miednicę w górę.",
                        "Gotowe, unieś biodra mocno do góry."
                    ])
                    assistant.speak(msg)
                    state = 2

                elif state == 2:
                    msg = random.choice([
                        "Dobra robota, podnieś prawą nogę.",
                        "Trzymaj biodra w górze i unieś prawą nogę.",
                        "Super, teraz prawa noga wędruje w górę.",
                        "Dobra robota, podnieś prawą nogę wysoko."
                    ])
                    assistant.speak(msg)
                    state = 3

                elif state == 3:
                    if "raised" in metrics:
                        prev_raised_leg = metrics["raised"]["name"]

                    msg = random.choice([
                        "Super. Teraz zmień nogę, lewa w górę.",
                        "Pięknie. Opuść prawą i od razu podnieś lewą nogę.",
                        "Dobra, zamieniamy strony. Lewa noga w górę.",
                        "Super. Teraz zmień nogę, lewa w górę i utrzymaj biodra wysoko."
                    ])
                    assistant.speak(msg)
                    state = 4

                elif state == 4:
                    reps += 1

                    if reps == 1:
                        msg = random.choice([
                            "Dobra robota, jedno powtórzenie za tobą. Zaczynamy kolejne, opuść biodra.",
                            "Świetny start, pierwsze powtórzenie gotowe. Wracamy na matę.",
                            "Mamy to! Jedno za nami. Opuść biodra i jedziemy dalej."
                        ])
                    else:
                        msg = random.choice([
                            f"Dobra robota, zrobiliśmy już {reps} powtórzenia. Zaczynamy kolejne, opuść biodra.",
                            f"Świetnie ci idzie, to już {reps} powtórzenie. Wracamy na matę.",
                            f"Super! Mamy {reps} powtórzeń na koncie. Odłóż biodra i jedziemy dalej."
                        ])

                    assistant.speak(msg)
                    state = 1
                    prev_raised_leg = None

                frames_held = 0
                error_cooldown = 0
                consecutive_errors = 0

        else:
            frames_held = max(0, frames_held - 1)

            consecutive_errors += 1
            if error_cooldown > 0:
                error_cooldown -= 1

            if consecutive_errors > ERROR_THRESHOLD and error_cooldown == 0:
                failed_side = [k for k, v in checks_side.items() if not v]
                failed_front = [k for k, v in checks_front.items() if not v]

                if len(checks_side) > 0 and 0 < len(failed_side) <= 3:
                    err_key = failed_side[0]
                    if err_key in ERROR_MESSAGES_SIDE:
                        assistant.speak(ERROR_MESSAGES_SIDE[err_key])
                        error_cooldown = COOLDOWN_FRAMES
                        consecutive_errors = 0

                elif len(checks_front) > 0 and 0 < len(failed_front) <= 2:
                    err_key = failed_front[0]
                    if err_key in ERROR_MESSAGES_FRONT:
                        assistant.speak(ERROR_MESSAGES_FRONT[err_key])
                        error_cooldown = COOLDOWN_FRAMES
                        consecutive_errors = 0

        combined = cv2.hconcat([view_side, view_front])

        cv2.putText(
            combined,
            f"POWTORZENIA: {reps}",
            (view_side.shape[1] - 230, combined.shape[0] - 40),
            cv2.FONT_HERSHEY_TRIPLEX,
            0.7,
            YELLOW,
            1,
            cv2.LINE_AA
        )

        if frames_held > 0:
            bar_w = int(400 * (frames_held / current_required))
            cv2.rectangle(combined, (20, combined.shape[0] - 20), (20 + bar_w, combined.shape[0] - 10), GREEN, -1)

        cv2.imshow(WINDOW_NAME, combined)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key in (ord('n'), ord('N')):
            assistant.stop_requested = True
        elif key in (ord('m'), ord('M')):
            skeleton_only = not skeleton_only

    cap_front.release()
    cap_side.release()
    close_pose_models()
    cv2.destroyAllWindows()

    return reps


if __name__ == "__main__":
    main()