import tkinter as tk
from threading import Thread
import time
from .gmail_api import connect_to_gmail_api, fetch_tcgplayer_email
from .task_relist_quantity import relist_quantity
import cc

# Global variable for checkbox
checkbox_var = None

def create_relister_gui():
    global checkbox_var
    print("=== Initializing Relister GUI ===")

    def continuous_gmail_checker():
        print("\n=== Starting Continuous Gmail Checker Loop ===")
        while True:
            print("inside while true")
            try:
                state = checkbox_var.get()
                print(f"Checkbox value type: {type(state)}, value: {state}")
            except Exception as e:
                print(f"Error getting checkbox state: {e}")
            
            if checkbox_var and checkbox_var.get():
                print("\n=== Running Gmail Check Cycle ===")
                try:
                    print("Connecting to Gmail...")
                    service = connect_to_gmail_api()
                    if service:
                        print("Gmail connection successful. Fetching sales data...")
                        sales_data = fetch_tcgplayer_email(service)
                        print(f"Fetched Sales Data: {sales_data}")
                        if sales_data:
                            send_to_worker = relist_quantity(sales_data)
                            cc.set_task_queue(send_to_worker)
                        print("Check cycle completed.")
                    else:
                        print("Failed to connect to Gmail. No service returned.")
                except Exception as e:
                    print(f"!!! ERROR in Gmail Checker: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
           
            print("Waiting 60 seconds until next check cycle...")
            time.sleep(60)

    def run_relist_test():
        print("\n=== Relister Test Function Started ===")
        try:
            send_to_worker = relist_quantity({"Arcane Signet": 1})
            print("Relister Test Completed.")
            cc.set_task_queue(send_to_worker)
            print("sent to worker")
        except Exception as e:
            print(f"!!! ERROR in Relister Test: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def on_checkbox_change():
        try:
            current = checkbox_var.get()
            checkbox_var.set(not current)  # Explicitly toggle the value
            print(f"Checkbox clicked! Previous: {current}, New: {checkbox_var.get()}")
        except Exception as e:
            print(f"Error in checkbox change: {e}")

    root = tk.Tk()
    root.title("Relister Control")

    # Initialize the global checkbox_var
    checkbox_var = tk.BooleanVar(value=False)
    checkbox = tk.Checkbutton(
        root,
        text="Enable Gmail Checker",
        variable=checkbox_var,
        command=on_checkbox_change
    )
    checkbox.pack(pady=10)

    # Start the eternal checker loop immediately
    Thread(target=continuous_gmail_checker, daemon=True).start()

    # Button for Relister Test
    test_button = tk.Button(
        root,
        text="Relister Test",
        command=lambda: Thread(target=run_relist_test, daemon=True).start()
    )
    test_button.pack(pady=10)

    print("Starting Relister GUI...")
    root.mainloop()
    print("Relister GUI Closed.")

def start_relister():
    print("\n=== Starting Relister ===")
    create_relister_gui()

if __name__ == "__main__":
    start_relister()