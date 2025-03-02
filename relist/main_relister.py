import tkinter as tk
from threading import Thread
import time
from .gmail_api import connect_to_gmail_api, fetch_tcgplayer_email
from .task_relist_quantity import relist_quantity
import cc
import json

# Global variable for checkbox
checkbox_var = None

def load_inventory():
    """Load inventory data from database.json"""
    try:
        with open("database.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: database.json not found.")
        return []
    except json.JSONDecodeError:
        print("Error: database.json is not valid JSON.")
        return []

def can_relist(card_name, inventory_data):
    """Check if a card has enough inventory to relist"""
    for card in inventory_data:
        if card["Name"] == card_name:
            current_qty = card["Inventory"].get("Current Quantity", 0)
            
            # Handle case where Critical Quantity is missing
            if "Critical Quantity" not in card["Inventory"]:
                print(f"Note: {card_name} doesn't have Critical Quantity set, using default threshold of 0")
                critical_qty = 0
            else:
                critical_qty = card["Inventory"]["Critical Quantity"]
                
            if current_qty > critical_qty:
                return True
            else:
                print(f"Skipping {card_name}: Current quantity ({current_qty}) not above critical quantity ({critical_qty})")
                return False
    print(f"Skipping {card_name}: Not found in inventory database")
    return False

def update_inventory(card_name, quantity_sold):
    """Update inventory by subtracting the sold quantity"""
    try:
        with open("database.json", "r") as file:
            inventory_data = json.load(file)
            
        # Find the card and update it
        updated = False
        for card in inventory_data:
            if card["Name"] == card_name:
                current_qty = card["Inventory"]["Current Quantity"]
                card["Inventory"]["Current Quantity"] = current_qty - quantity_sold
                updated = True
                print(f"Updated inventory for {card_name}: {current_qty} -> {card['Inventory']['Current Quantity']}")
                break
                
        if updated:
            # Save the updated inventory
            with open("database.json", "w") as file:
                json.dump(inventory_data, file, indent=4)
            return True
        else:
            print(f"Warning: Card {card_name} not found in inventory")
            return False
            
    except Exception as e:
        print(f"Error updating inventory: {e}")
        return False

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
                            # Load inventory data
                            inventory_data = load_inventory()
                            
                            # Filter sales data based on inventory availability
                            filtered_sales_data = {}
                            for card, qty in sales_data.items():
                                if can_relist(card, inventory_data):
                                    filtered_sales_data[card] = qty
                            
                            # Only proceed if we have cards to relist
                            if filtered_sales_data:
                                print(f"Relisting {len(filtered_sales_data)} cards that have sufficient inventory")
                                send_to_worker = relist_quantity(filtered_sales_data)
                                cc.set_task_queue(send_to_worker)
                                
                                # Update inventory for each card that was relisted
                                for card_name, qty in filtered_sales_data.items():
                                    update_inventory(card_name, qty)
                            else:
                                print("No cards have sufficient inventory for relisting")
                                
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
            # Original test cards
            test_cards = {"Arcane Signet": 1, "Nest Ball": 1}
            
            # Check inventory before relisting
            inventory_data = load_inventory()
            filtered_test_cards = {}
            
            for card_name, qty in test_cards.items():
                if can_relist(card_name, inventory_data):
                    filtered_test_cards[card_name] = qty
                    
            if filtered_test_cards:
                # Original behavior - send each card separately
                for card_name, qty in filtered_test_cards.items():
                    send_to_worker = relist_quantity({card_name: qty})
                    cc.set_task_queue(send_to_worker)
                    # Update inventory after relisting
                    update_inventory(card_name, qty)
                print("Relister Test Completed.")
                print("sent to worker")
            else:
                print("Test aborted: No cards have sufficient inventory")
                
        except Exception as e:
            print(f"!!! ERROR in Relister Test: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    # Keep your original checkbox change handler
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