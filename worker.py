import zmq
import logging
import pyautogui
import time
import sys
import mss
import cv2
import numpy as np
import uuid
import socket as sock

# Define log file in the same directory as worker.py
LOG_FILE = "worker_actions.log"

# Configure logging to store logs in a file (but NOT print them)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode='a')]  # 'a' appends instead of overwriting
)

# Server configuration
CNC_SERVER_IP = "192.168.50.58"
CNC_SERVER_PORT = 6000

# Worker configuration
WORKER_ID = f"worker-{uuid.uuid4().hex[:8]}"  # Generate unique worker ID
FUNCTION_TYPE = "default"  # Can be "relisting", or "default"
HEARTBEAT_INTERVAL = 30  # Seconds between heartbeats

# Create ZMQ context (only need to do this once)
context = zmq.Context()

# IMPORTANT!!! Logging.info saves to the text file, print saves to the console. You must do them separately.

def send_message(socket, message, timeout=10):
    """
    Send a message and wait for a response with timeout.
    Returns the response or None if timeout occurs.
    """
    try:
        socket.send_string(message)
        if socket.poll(timeout * 1000) & zmq.POLLIN:
            return socket.recv_string()
        else:
            logging.error(f"Timeout waiting for response to: {message}")
            return None
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return None

def register_worker(socket):
    """
    Register worker with the server.
    """
    response = send_message(socket, f"REGISTER:{WORKER_ID}:{FUNCTION_TYPE}")
    if response == "REGISTERED":
        logging.info(f"Successfully registered as {WORKER_ID} for {FUNCTION_TYPE}")
        print(f"Successfully registered as {WORKER_ID} for {FUNCTION_TYPE}")
        return True
    return False

def send_heartbeat(socket):
    """
    Send heartbeat to the server.
    """
    response = send_message(socket, f"HEARTBEAT:{WORKER_ID}")
    if response == "HEARTBEAT_ACK":
        logging.debug(f"Heartbeat acknowledged")
        return True
    elif response == "REGISTER_REQUIRED":
        logging.warning("Server doesn't recognize this worker, re-registering...")
        return register_worker(socket)
    return False

def notify_task_complete(socket):
    """
    Notify the server that task is complete.
    """
    response = send_message(socket, f"TASK_COMPLETE:{WORKER_ID}")
    if response == "ACK":
        logging.info("Server acknowledged task completion")
        return True
    elif response == "REGISTER_REQUIRED":
        logging.warning("Server doesn't recognize this worker, re-registering...")
        return register_worker(socket)
    return False

def request_task(socket):
    """
    Request a task from the server.
    Returns the task or None if no tasks or error.
    """
    response = send_message(socket, f"GET_TASK:{WORKER_ID}")
    
    if response == "NO_TASKS":
        logging.info("No tasks available")
        print("No tasks available")
        return None
    elif response == "BUSY":
        logging.info("Worker is marked as busy on server")
        print("Worker is marked as busy on server")
        return None
    elif response == "REGISTER_REQUIRED":
        logging.warning("Server doesn't recognize this worker, re-registering...")
        register_worker(socket)
        return None
    else:
        return response

# Main worker loop
while True:
    socket = None
    try:
        # Create and connect socket
        socket = context.socket(zmq.REQ)
        socket.setsockopt(zmq.LINGER, 0)  # Don't wait for unsent messages when closing
        logging.info("Attempting to connect to server...")
        print("Attempting to connect to server...")
        sys.stdout.flush()
        socket.connect(f"tcp://{CNC_SERVER_IP}:{CNC_SERVER_PORT}")
        logging.info("Connected to server")
        print("Connected to server")
        sys.stdout.flush()
        
        # Register with the server
        if not register_worker(socket):
            logging.error("Failed to register with server")
            print("Failed to register with server")
            time.sleep(5)
            continue
            
        last_heartbeat = time.time()
        
        while True:  # Inner connection loop
            current_time = time.time()
            
            # Send heartbeat if needed
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                if send_heartbeat(socket):
                    last_heartbeat = current_time
                else:
                    logging.error("Failed to send heartbeat, reconnecting...")
                    break
            
            # Request a task
            print("Requesting task from server...")
            sys.stdout.flush()
            task = request_task(socket)
            
            if task is None:
                # No task available or worker is busy, wait before retrying
                time.sleep(5)
                continue
                
            # Convert the received string back into a Python list
            logging.info("Attempting to convert received task data to a Python list using eval()...")
            print("Attempting to convert received task data to a Python list using eval()...")
            sys.stdout.flush()
            
            try:
                task_queue = eval(task)
                logging.info(f"Successfully converted task data to a Python list. Task queue contains {len(task_queue)} tasks.")
                print(f"Successfully converted task data to a Python list. Task queue contains {len(task_queue)} tasks.")
                sys.stdout.flush()
            except Exception as e:
                logging.error(f"Error during eval() to convert task data to list: {e}")
                print(f"Error during eval() to convert task data to list: {e}")
                sys.stdout.flush()
                # Notify server of task failure
                notify_task_complete(socket)
                continue
                
            # Process tasks one by one and remove them immediately
            while task_queue:
                task_code = task_queue[0]
                sys.stdout.flush()
                
                try:
                    exec(task_code)
                    logging.info("Task execution completed successfully.")
                    print("Task execution completed successfully.")
                    sys.stdout.flush()
                except Exception as e:
                    logging.error(f"Error executing task: {task_code} - {e}")
                    print(f"Error executing task: {task_code} - {e}")
                    sys.stdout.flush()
                    
                del task_queue[0]
                logging.info(f"Task removed from queue. Remaining tasks: {len(task_queue)}")
                print(f"Task removed from queue. Remaining tasks: {len(task_queue)}")
                sys.stdout.flush()
            
            logging.info("All tasks in the received queue have been processed.")
            print("All tasks in the received queue have been processed.")
            sys.stdout.flush()
            
            # Notify server that we're done and ready for more tasks
            notify_task_complete(socket)

    except zmq.ZMQError as e:
        logging.error(f"ZMQ error: {e}. Retrying in 5 seconds.")
        print(f"ZMQ error: {e}. Retrying in 5 seconds.")
        sys.stdout.flush()
        time.sleep(5)
    except Exception as e:
        logging.error(f"General error: {e}")
        print(f"General error: {e}")
        sys.stdout.flush()
        time.sleep(5)
    finally:
        if socket:
            try:
                socket.close()
            except Exception as e:
                logging.error(f"Error closing socket: {e}")
                print(f"Error closing socket: {e}")
                sys.stdout.flush()