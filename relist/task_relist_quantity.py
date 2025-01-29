from .relist_worker import format_task_code, minimize_screen, open_browser, navigate_to_webpage, relist_card
#from .relist_switch import check_screen_state

def relist_quantity(sales_data):
    print("=== Starting Relist Quantity ===")

    # Initialize task queue
    task_queue = []

    # Step 1: Minimize all windows
    print("Step 1: Minimizing all windows...")
    minimize_screen_code = format_task_code(minimize_screen)  # Call relist_worker to prepare the code
    task_queue.append(minimize_screen_code)   # Add the prepared task code to the queue
    #print(f"Minimize code: {minimize_screen_code}")
    
    print("Step2: Opening Brave...")
    open_browser_code = format_task_code(open_browser)
    task_queue.append(open_browser_code)
    
    for card_name in sales_data.keys():
        print(f"Step 3: Navigate to webpage for {card_name}")
        navigate_to_webpage_code = format_task_code(navigate_to_webpage, card_name)  # Defer execution
        task_queue.append(navigate_to_webpage_code)

    print("Step 4: relist card")
    relist_card_code = format_task_code(relist_card)
    task_queue.append(relist_card_code)
    return task_queue