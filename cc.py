import zmq
import threading
import logging
import json
import time
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Server configuration
PORT = 6000

# Task queue for different function types
task_queues = {
    "relisting": [],
    "default": []
}

# Worker tracking dictionary
workers = {}

# Heartbeat timeout (seconds)
HEARTBEAT_TIMEOUT = 60

def set_task_queue(queue, function_type="default"):
    """
    Add a task queue to the outer queue.
    
    Args:
        queue: List of tasks to be executed
        function_type: Type of function this task is for (default, relisting)
    """
    global task_queues
    
    if function_type not in task_queues:
        function_type = "default"
    
    task_queues[function_type].append(queue)
    logging.info(f"Added a task queue with {len(queue)} tasks to {function_type}. Total queues: {len(task_queues[function_type])}")

def is_worker_available(worker_id):
    """
    Check if a worker is available based on heartbeat and status.
    """
    if worker_id not in workers:
        return False
        
    # Check heartbeat is recent
    current_time = time.time()
    last_heartbeat = workers[worker_id]["Heartbeat"]
    
    if current_time - last_heartbeat > HEARTBEAT_TIMEOUT:
        # Worker has timed out, remove it from tracking
        logging.warning(f"Worker {worker_id} heartbeat timeout. Removing from tracking.")
        del workers[worker_id]
        return False
        
    # Check if worker is available
    return workers[worker_id]["Availability"]

def handle_worker_connection(socket):
    """
    Handle communication with a single worker.
    :param socket: ZMQ socket for the connection.
    """
    try:
        while True:
            # Wait for worker request
            message = socket.recv_string()
            logging.info(f"Received message: {message}")
            
            # Handle different message types
            if message.startswith("REGISTER:"):
                # Register a new worker or update existing one
                parts = message.split(":")
                worker_id = parts[1]
                function_type = parts[2] if len(parts) > 2 else "default"
                
                # Register or update the worker
                if worker_id not in workers:
                    workers[worker_id] = {
                        "Name": worker_id,
                        "FunctionAssignment": function_type,
                        "Availability": True,
                        "Heartbeat": time.time()
                    }
                    logging.info(f"New worker registered: {worker_id} for {function_type}")
                else:
                    # Update existing worker
                    workers[worker_id]["Heartbeat"] = time.time()
                    workers[worker_id]["FunctionAssignment"] = function_type
                    logging.info(f"Updated worker: {worker_id} for {function_type}")
                
                # Send acknowledgment
                socket.send_string("REGISTERED")
                
            elif message.startswith("HEARTBEAT:"):
                # Update worker heartbeat
                worker_id = message.split(":")[1]
                if worker_id in workers:
                    workers[worker_id]["Heartbeat"] = time.time()
                    socket.send_string("HEARTBEAT_ACK")
                else:
                    # Worker not registered
                    socket.send_string("REGISTER_REQUIRED")
                
            elif message.startswith("TASK_COMPLETE:"):
                # Worker has completed a task
                worker_id = message.split(":")[1]
                if worker_id in workers:
                    workers[worker_id]["Availability"] = True
                    socket.send_string("ACK")
                    logging.info(f"Worker {worker_id} is now available")
                else:
                    socket.send_string("REGISTER_REQUIRED")
            
            elif message.startswith("GET_TASK:"):
                # Worker is requesting a task
                parts = message.split(":")
                worker_id = parts[1]
                
                # Make sure worker is registered
                if worker_id not in workers:
                    socket.send_string("REGISTER_REQUIRED")
                    continue
                
                # Update heartbeat
                workers[worker_id]["Heartbeat"] = time.time()
                
                # Check if worker is available
                if not workers[worker_id]["Availability"]:
                    socket.send_string("BUSY")
                    continue
                
                # Get worker's function assignment
                function_type = workers[worker_id]["FunctionAssignment"]
                
                # Check for tasks in the assigned queue
                if function_type in task_queues and task_queues[function_type]:
                    next_queue = task_queues[function_type].pop(0)
                    workers[worker_id]["Availability"] = False
                    socket.send_string(str(next_queue))
                    logging.info(f"Sent task queue with {len(next_queue)} tasks to worker {worker_id}")
                else:
                    # Check default queue if no specialized tasks
                    if task_queues["default"]:
                        next_queue = task_queues["default"].pop(0)
                        workers[worker_id]["Availability"] = False
                        socket.send_string(str(next_queue))
                        logging.info(f"Sent default task queue with {len(next_queue)} tasks to worker {worker_id}")
                    else:
                        socket.send_string("NO_TASKS")
                        print(f"No tasks available for worker {worker_id}")
            
            else:
                # Unknown message
                logging.warning(f"Unknown message: {message}")
                socket.send_string("UNKNOWN_COMMAND")
                
    except zmq.ZMQError as e:
        logging.error(f"ZMQ Error: {e}")
    except Exception as e:
        logging.error(f"Error: {e}")

def start_cc():
    """
    Start the CC server to listen for workers.
    """
    def server_thread():
        context = zmq.Context()
        socket = context.socket(zmq.REP)
       
        try:
            socket.bind(f"tcp://*:{PORT}")
            logging.info(f"CC server listening on port {PORT}")
           
            while True:
                handle_worker_connection(socket)
               
        except KeyboardInterrupt:
            logging.info("Shutting down CC server.")
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            socket.close()
            context.term()
            
    threading.Thread(target=server_thread, daemon=True).start()

def stop_cc():
    """
    Placeholder for stopping the CC server.
    For now, this is a no-op since we're using daemon threads.
    """
    logging.info("CC server stop requested, but not implemented.")