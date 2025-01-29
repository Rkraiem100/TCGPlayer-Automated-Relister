# main.py
import tkinter as tk
import threading
import json
import os
import sys
from cc import start_cc, stop_cc
from relist.main_relister import start_relister

# Global variable for the database
global_database = {
    "cards": {},  # Stores card data
    "metadata": {},  # Additional metadata
}

# Helper function to load database from JSON
def load_database():
    global global_database
    if os.path.exists("database.json"):
        with open("database.json", "r") as f:
            global_database = json.load(f)
    else:
        print("No database.json file found. Starting with an empty database.")

# Helper function to save database to JSON
def save_database():
    global global_database
    with open("database.json", "w") as f:
        json.dump(global_database, f, indent=4)

# Function to launch a sub-program in a separate thread
def launch_sub_program(module_name):
    def run_module():
        if module_name == "Relister/main_relister.py":
            start_relister()
        else:
            os.system(f"python {module_name}")
    thread = threading.Thread(target=run_module)
    thread.daemon = True
    thread.start()

# GUI logic
def create_gui():
    def toggle_program():
        if enabled_var.get():
            print("Program enabled.")
            start_cc()  # Start the CC system
        else:
            print("Program disabled.")
            stop_cc()  # Stop the CC system

    root = tk.Tk()
    root.title("Program Control")

    # Checkbox for enabling/disabling the program
    enabled_var = tk.BooleanVar(value=False)
    enable_checkbox = tk.Checkbutton(
        root, text="Enabled", variable=enabled_var, command=toggle_program
    )
    enable_checkbox.pack(pady=10)

    # Buttons for launching sub-programs
    relister_button = tk.Button(
        root, text="Launch Relister", command=lambda: launch_sub_program("Relister/main_relister.py")
    )
    relister_button.pack(pady=5)

    scraper_button = tk.Button(
        root, text="Launch Scraper", command=lambda: launch_sub_program("Scraper/main_scraper.py")
    )
    scraper_button.pack(pady=5)

    trends_button = tk.Button(
        root, text="Launch Trends", command=lambda: launch_sub_program("Trends/main_trends.py")
    )
    trends_button.pack(pady=5)

    root.mainloop()

# Main entry point
if __name__ == "__main__":
    load_database()  # Load the database on start
    create_gui()  # Start the GUI
    save_database()  # Save the database on exit