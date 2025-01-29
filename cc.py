import zmq
import threading
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Server configuration
PORT = 6000
task_queue = []

def set_task_queue(queue):
    """
    Add a task queue to the outer queue.
    """
    global task_queue
    task_queue.append(queue)
    #print(f"FULL TASK QUEUE SENT TO WORKER: {task_queue}")
    logging.info(f"Added a task queue with {len(queue)} tasks. Total queues: {len(task_queue)}")

def handle_worker_connection(socket):
    """
    Handle communication with a single worker.
    :param socket: ZMQ socket for the connection.
    """
    try:
        while True:
            # Wait for worker request
            message = socket.recv_string()
            logging.info(f"Received request: {message}")

            if message == "GET_TASK":
                global task_queue
                if task_queue:
                    next_queue = task_queue.pop(0)  # Get the first inner queue
                    socket.send_string(str(next_queue))  # Send as string instead of JSON
                    logging.info(f"Sent task queue with {len(next_queue)} tasks to worker")
                else:
                    socket.send_string("NO_TASKS")
                    logging.info("No task queues available for worker")
            else:
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