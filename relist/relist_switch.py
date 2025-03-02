#relist_switch.py
def handle_state(state):
    import os
    import pyautogui
    import time
    import cv2
    import numpy as np



    match state:
        case "desktop":
            
            DESKTOP_IMAGE = "C:\\WorkerImages\\Desktop.png"
            if pyautogui.locateOnScreen(DESKTOP_IMAGE, confidence=0.3):
                print("Desktop detected. Proceeding...")
                return "desktop_verified"
            else:
                print("Broken, desktop not verified looping attempt to minimize")
                globals()['minimize_screen']()  # Use dynamic lookup instead of direct call
                return "BROKEN!"

        case "brave_open":
            BRAVE_OPEN = "C:\\WorkerImages\\BraveOpen.png"
            if pyautogui.locateOnScreen(BRAVE_OPEN, confidence=0.3):
                print("Brave browser detected in a new tab. Proceeding...")
                return "Brave Open"
            else:
                print("BRAVE NOT OPENED WAITING 5 SECONDS")
                time.sleep(5)
                return "POSSIBLE ERROR"

        case "is_signin_page":
            print("Entered sign-in switch...")
            SIGN_IN = "C:\\WorkerImages\\Signin0.png"
            try:
                # Perform template matching
                _, max_val, _, _ = cv2.minMaxLoc(cv2.matchTemplate(cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR), cv2.imread(SIGN_IN), cv2.TM_CCOEFF_NORMED))
                # Confidence threshold check
                if max_val >= 0.7:  # Adjust the threshold as needed
                    print(f"Sign-in page detected with confidence {max_val}")
                    return True
                else:
                    print("Different page detected")
                    return False
            except Exception as e:
                print(f"Error type: {type(e)}")
                print(f"Error in sign-in detection: {str(e)}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                return False

            

        case "captcha":
            print("Captcha detected. Redirecting to captcha handling...")
            return "handle_captcha"

        case "unknown":
            print("Unknown state detected. Retrying...")
            time.sleep(2)  # Pause before retrying
            return "retry"

        case _:
            print("Unhandled state. No action taken.")
            return "no_action"
