#relist_worker.py
import logging
import cc
import inspect

logging.info(f"relist_worker.py using cc module at: {cc.__file__}")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def minimize_screen():
    import pyautogui
    import time
    import logging
    
    logging.info("Minimizing all windows...")
    print("Minimizing all windows...")
    pyautogui.hotkey("win", "d")
    time.sleep(3)
    logging.info("Minimizing Windows Successful~")
    print("Minimizing Windows Successful~")
    #globals()['handle_state']("desktop")  # Use dynamic lookup

def open_browser():
    import psutil
    import subprocess
    import time
    import pygetwindow as gw

    BRAVE_PATH = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
    BRAVE_PROFILE_PATH = "C:\\BraveProfile"  # Profile directory to persist session
    DEBUGGING_PORT = 9222  # Set the remote debugging port

    logging.info("Attempting to open Brave")
    print("Attempting to open Brave")
    # Check if Brave is already running
    brave_running = False
    for process in psutil.process_iter(['name']):
        if "brave.exe" in process.info['name'].lower():
            brave_running = True
            logging.info("Brave is already running.")
            print("Brave is already running.")
            break

    # Open Brave with remote debugging if it's not running
    if not brave_running:
        print("Launching Brave Browser with debugging enabled...")
        logging.info("Launching Brave Browser with debugging enabled...")

        subprocess.Popen(
            [BRAVE_PATH, f"--remote-debugging-port={DEBUGGING_PORT}", f"--user-data-dir={BRAVE_PROFILE_PATH}"],
            shell=True
        )
        time.sleep(5)  # Give Brave some time to fully open

    # Bring Brave to the front
    time.sleep(1)  # Allow time for windows to register
    brave_windows = [w for w in gw.getWindowsWithTitle("Brave") if w.title]
    if brave_windows:
        brave_window = brave_windows[0]  # First matching window
        print("Bringing Brave to front...")
        logging.info("Bringing Brave to front...")
        brave_window.maximize()  # Maximize the window
        brave_window.activate()  # This replaces win32gui.SetForegroundWindow
    else:
        logging.info("Brave window not found. It may still be launching.")
        print("Brave window not found. It may still be launching.")

    #globals()['handle_state']("brave_open")

def navigate_to_webpage():
    import pyautogui
    import time
    import cv2
    import numpy as np

    card_url = CARD_DATA.get(CURRENT_CARD) 
    if not card_url:
        raise ValueError(f"Card '{CURRENT_CARD}' not found in CARD_DATA.")

    TARGET_URL = card_url["url"]

    # Small pause to ensure window is ready
    time.sleep(1)

    # Paste URL and press enter
    pyautogui.hotkey('ctrl', 'l')  # Select address bar
    time.sleep(0.5)
    pyautogui.typewrite(TARGET_URL)
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(5)

    case = globals()['handle_state']("is_signin_page")

    if case == True:
        SIGNIN1 = "C:\\WorkerImages\\Signin1.png"
        SIGNIN2 = "C:\\WorkerImages\\Signin2.png"
        SIGNIN3 = "C:\\WorkerImages\\Signin3.png"
        SIGNIN4 = "C:\\WorkerImages\\Signin4.png"
        SIGNIN5 = "C:\\WorkerImages\\Signin5.png"
        print("Inside sign-in if statement...")
        logging.info("Inside sign-in if statement...")


        template1 = cv2.imread(SIGNIN1)  # Load template image
        _, max_val1, _, max_loc1 = cv2.minMaxLoc(cv2.matchTemplate(cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR), template1, cv2.TM_CCOEFF_NORMED))
        if max_val1 >= 0.7:  # Confidence threshold
            print(f"SIGNIN1 detected with confidence {max_val1}")
            logging.info(f"SIGNIN1 detected with confidence {max_val1}")
            pyautogui.click(max_loc1[0] + template1.shape[1] // 2, max_loc1[1] + template1.shape[0] // 2)
            time.sleep(0.5)

        template2 = cv2.imread(SIGNIN2)  # Load template image
        _, max_val2, _, max_loc2 = cv2.minMaxLoc(cv2.matchTemplate(cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR), template2, cv2.TM_CCOEFF_NORMED))
        if max_val2 >= 0.7:  # Confidence threshold
            print(f"SIGNIN2 detected with confidence {max_val2}")
            logging.info(f"SIGNIN2 detected with confidence {max_val2}")
            pyautogui.click(max_loc2[0] + template2.shape[1] // 2, max_loc2[1] + template2.shape[0] // 2 - 30)
            time.sleep(0.5)
            
        template3 = cv2.imread(SIGNIN3)  # Load template image
        _, max_val3, _, max_loc3 = cv2.minMaxLoc(cv2.matchTemplate(cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR), template3, cv2.TM_CCOEFF_NORMED))
        if max_val3 >= 0.7:
            print(f"SIGNIN3 detected with confidence {max_val3}. Clicking Remember Me")
            logging.info(f"SIGNIN3 detected with confidence {max_val3}. Clicking Remember Me")
            pyautogui.click(max_loc3[0] + template3.shape[1] // 2, max_loc3[1] + template3.shape[0] // 2)
            time.sleep(0.5)
        
        template5 = cv2.imread(SIGNIN5)  # Load template image
        _, max_val5, _, max_loc5 = cv2.minMaxLoc(cv2.matchTemplate(cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR), template5, cv2.TM_CCOEFF_NORMED))
        if max_val5 >= 0.7:
            print(f"SIGNIN5 detected with confidence {max_val5}. Logging In")
            logging.info(f"SIGNIN5 detected with confidence {max_val5}. Logging In")
            pyautogui.click(max_loc5[0] + template5.shape[1] // 2, max_loc5[1] + template5.shape[0] // 2)
            time.sleep(0.5)


        time.sleep(3)

def relist_card():
    import pyautogui
    import time
    import cv2
    import numpy as np

    time.sleep(0.5)

    DEFAULT_QUANTITY = CARD_DATA.get(CURRENT_CARD, {}).get("default_quantity")
    if DEFAULT_QUANTITY is None:
        raise ValueError(f"Card '{CURRENT_CARD}' not found in CARD_DATA or missing 'default_quantity'.")

    RELIST1 = "C:\\WorkerImages\\Relist1.png"
    RELIST2 = "C:\\WorkerImages\\Relist2.png"
    RELIST3 = "C:\\WorkerImages\\Relist3.png"


    print("Attempting to relist")
    logging.info("Attempting to relist")


    template1 = cv2.imread(RELIST1)  # Near Mint template
    template2 = cv2.imread(RELIST2)  # Total Qty template
    template3 = cv2.imread(RELIST3)  # Save Changes

    # Get screenshot once and convert it
    screenshot = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)

    # Find both templates
    _, max_val1, _, max_loc1 = cv2.minMaxLoc(cv2.matchTemplate(screenshot, template1, cv2.TM_CCOEFF_NORMED))
    _, max_val2, _, max_loc2 = cv2.minMaxLoc(cv2.matchTemplate(screenshot, template2, cv2.TM_CCOEFF_NORMED))
    _, max_val3, _, max_loc3 = cv2.minMaxLoc(cv2.matchTemplate(screenshot, template3, cv2.TM_CCOEFF_NORMED))


    # If both are found with good confidence
    if max_val1 >= 0.7 and max_val2 >= 0.7:
        print(f"Near Mint detected at {max_loc1} with confidence {max_val1}")
        logging.info(f"Near Mint detected at {max_loc1} with confidence {max_val1}")
        print(f"Total Qty detected at {max_loc2} with confidence {max_val2}")
        logging.info(f"Total Qty detected at {max_loc2} with confidence {max_val2}")


        # Click at Total Qty X position but Near Mint Y position
        click_x = max_loc2[0] + template2.shape[1] // 2
        click_y = max_loc1[1] + template1.shape[0] // 2

        pyautogui.click(click_x, click_y)
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        #pyautogui.hotkey('1')
        time.sleep(0.1)
        #pyautogui.click(max_loc3[0] + template3.shape[1] // 2, max_loc3[1] + template3.shape[0] // 2)
        pyautogui.write(str(DEFAULT_QUANTITY))

        if max_val3 >= 0.7:
            print(f"Save Changes button detected at {max_loc3} with confidence {max_val3}")
            logging.info(f"Save Changes button detected at {max_loc3} with confidence {max_val3}")
            pyautogui.click(max_loc3[0] + template3.shape[1] // 2, max_loc3[1] + template3.shape[0] // 2)
        else:
            print("Save Changes button not found with sufficient confidence.")
            logging.info("Save Changes button not found with sufficient confidence.")



import os

def format_task_code(func, card_name=None):
    """
    Format a given function as task code (string) for the worker.
    Extracts the full source code of the function, injects dependencies like handle_state,
    and appends a call to execute it.
    """
    import inspect
    import json
    from .relist_switch import handle_state  # Import handle_state to extract its code

    # Extract the raw source code of handle_state
    switch_code = inspect.getsource(handle_state)

    # Extract the raw source code of the passed function (e.g., minimize_screen)
    task_code = inspect.getsource(func)

    # Load relist_instructions.json and embed it as a string
    json_path = os.path.join(os.path.dirname(__file__), "relist_instructions.json")
    try:
        with open(json_path, "r") as f:
            json_data = json.load(f)
        json_blob = json.dumps(json_data, indent=4)  # Convert JSON to a string for embedding
    except FileNotFoundError as e:
        raise RuntimeError(f"Could not find {json_path} during task packaging.") from e
    
    current_card = f"CURRENT_CARD = '{card_name}'" if card_name else ""

    # Combine everything into the complete task code
    complete_code = f"""
import sys
import json
{current_card}
CARD_DATA = json.loads('''{json_blob}''')
{switch_code}
{task_code}
{func.__name__}()  # Call the function
"""

    return complete_code


    