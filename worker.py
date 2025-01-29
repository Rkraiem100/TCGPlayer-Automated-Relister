import zmq
import logging
import pyautogui
import time
import sys
import mss
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CNC_SERVER_IP = "0.0.0.0" #REPLACE WITH THE IP ADDRESS OF THE SERVER!
CNC_SERVER_PORT = 6000

# Create ZMQ context (only need to do this once)
context = zmq.Context()

while True:
    socket = None
    try:
        # Create and connect socket
        socket = context.socket(zmq.REQ)
        logging.info("Attempting to connect to server...")
        sys.stdout.flush()
        socket.connect(f"tcp://{CNC_SERVER_IP}:{CNC_SERVER_PORT}")
        logging.info("Connected to server")
        sys.stdout.flush()

        while True:  # Inner connection loop
            # Request tasks from the server
            logging.info("Sending GET_TASK request to server...")
            sys.stdout.flush()
            socket.send_string("GET_TASK")
           
            logging.info("Waiting to receive task data from server...")
            sys.stdout.flush()
            task = socket.recv_string()  # ZMQ handles message completeness
            logging.info(f"Received raw task data from server: {task}")
            sys.stdout.flush()

            if task == "NO_TASKS":
                logging.info("Received NO_TASKS from server. Waiting before retrying.")
                time.sleep(5)
                sys.stdout.flush()
                continue

            # Convert the received string back into a Python list
            logging.info("Attempting to convert received task data to a Python list using eval()...")
            sys.stdout.flush()
            try:
                task_queue = eval(task)
                logging.info(f"Successfully converted task data to a Python list. Task queue contains {len(task_queue)} tasks.")
                sys.stdout.flush()
            except Exception as e:
                logging.error(f"Error during eval() to convert task data to list: {e}")
                sys.stdout.flush()
                break  # Break inner loop to reconnect

            # Process tasks one by one and remove them immediately
            while task_queue:
                task_code = task_queue[0]
                logging.info(f"About to execute task: {task_code}")
                sys.stdout.flush()
                try:
                    # Replace pyautogui.screenshot() with mss for reliability
                    def capture_screenshot():
                        try:
                            with mss.mss() as sct:
                                monitor = sct.monitors[1]  # Adjust index if needed
                                return cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_RGB2BGR)
                        except Exception as e:
                            logging.error(f"Error capturing screenshot: {e}")
                            return None

                    # Example usage of screenshot replacement
                    screenshot = capture_screenshot()
                    if screenshot is None:
                        logging.error("Screenshot capture failed. Skipping task.")
                        del task_queue[0]
                        continue

                    exec(task_code)
                    logging.info("Task execution completed successfully.")
                    sys.stdout.flush()
                except Exception as e:
                    logging.error(f"Error executing task: {task_code} - {e}")
                    sys.stdout.flush()
                del task_queue[0]
                logging.info(f"Task removed from queue. Remaining tasks: {len(task_queue)}")
                sys.stdout.flush()
           
            logging.info("All tasks in the received queue have been processed. Requesting new tasks.")
            sys.stdout.flush()

    except zmq.ZMQError as e:
        logging.error(f"ZMQ error: {e}. Retrying in 5 seconds.")
        sys.stdout.flush()
        time.sleep(5)
    except Exception as e:
        logging.error(f"General error: {e}")
        sys.stdout.flush()
        time.sleep(5)
    finally:
        if socket:
            try:
                socket.close()
            except Exception as e:
                logging.error(f"Error closing socket: {e}")
                sys.stdout.flush()
