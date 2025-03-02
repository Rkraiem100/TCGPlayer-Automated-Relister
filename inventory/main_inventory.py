import tkinter as tk
from tkinter import ttk
import json
import os

# --- Helper Functions ---

def get_next_unique_id(database):
    """Scan the database for the highest ID and return the next one in the format 'IDx'."""
    max_num = 0
    for card in database:
        card_id = card.get("ID")
        if card_id and card_id.startswith("ID"):
            try:
                num = int(card_id[2:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"ID{max_num + 1}"

def generate_unique_name(base, row_by_id):
    """(Optional) Return a unique name based on 'base' using keys from row_by_id.
       Not used for lookup since we use IDs for uniqueness."""
    if base not in row_by_id:
        return base
    i = 1
    while f"{base} {i}" in row_by_id:
        i += 1
    return f"{base} {i}"

def treeview_values(card):
    """Return a tuple of values for the treeview from a card dict.
       (The unique ID is stored as the item id, so we do not display it here.)"""
    return (
        card.get("Name", "Unknown"),
        card.get("Game", "Unknown"),
        card.get("Rarity", "Unknown"),
        card.get("Set Code", "Unknown"),
        card.get("Inventory", {}).get("Current Quantity", 0),
        card.get("Inventory", {}).get("Average Paid Price", 0),
        card.get("Inventory", {}).get("Location", "Unknown")
    )

# --- Database Loading and Saving ---

def load_database():
    db_path = os.path.abspath(os.path.join(os.getcwd(), "database.json"))
    try:
        with open(db_path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_database(database):
    db_path = os.path.abspath(os.path.join(os.getcwd(), "database.json"))
    try:
        with open(db_path, "w") as f:
            json.dump(database, f, indent=4)
        print(f"Database saved to {db_path}")
    except Exception as e:
        print(f"Error saving database: {e}")

# --- Treeview Population and Updates ---

def populate_table(tree, database):
    """Fill the treeview with records from database and build a row mapping keyed by unique ID."""
    tree.row_by_id = {}
    for card in database:
        card_id = card.get("ID")
        if not card_id:
            card_id = get_next_unique_id(database)
            card["ID"] = card_id
        row_id = tree.insert("", "end", iid=card_id, values=treeview_values(card))
        tree.row_by_id[card_id] = row_id

def update_detailed_preview(row_id, tree, database, text):
    """
    Load the full JSON for the card with unique ID (row_id) into the detailed text.
    Also store the current card's ID in text.current_card_id.
    """
    card_id = row_id  # row_id is our unique card ID
    for card in database:
        if card.get("ID") == card_id:
            text.delete("1.0", tk.END)
            text.insert(tk.END, json.dumps(card, indent=4))
            text.current_card_id = card_id
            text.edit_modified(False)
            break

def sync_detailed_info(text, tree, database):
    """
    Parse the JSON from the detailed info text and update the matching card (using its unique ID).
    If the ID changes, update the mapping.
    """
    content = text.get("1.0", tk.END).strip()
    if not content:
        return
    try:
        updated_card = json.loads(content)
    except json.JSONDecodeError:
        print("Invalid JSON in detailed info.")
        return

    new_id = updated_card.get("ID")
    if not new_id:
        print("Card must have an ID.")
        return

    old_id = getattr(text, "current_card_id", new_id)
    for i, card in enumerate(database):
        if card.get("ID") == old_id:
            database[i] = updated_card
            row_id = tree.row_by_id.get(old_id)
            if row_id:
                if old_id != new_id:
                    del tree.row_by_id[old_id]
                    tree.row_by_id[new_id] = row_id
                    text.current_card_id = new_id
                tree.item(row_id, values=treeview_values(updated_card))
            break
    else:
        print(f"Card with ID '{old_id}' not found in database.")

def update_row_highlight(tree, row_id):
    """Highlight only the given row."""
    if hasattr(tree, 'selected_row') and tree.selected_row:
        tree.item(tree.selected_row, tags=())
    tree.item(row_id, tags=("row_light_blue",))
    tree.selected_row = row_id

def update_cell_highlight(tree, row_id, col_id):
    """Overlay a dark-blue label on the clicked cell."""
    if hasattr(tree, 'current_cell_highlight') and tree.current_cell_highlight:
        tree.current_cell_highlight.destroy()
        tree.current_cell_highlight = None
    bbox = tree.bbox(row_id, col_id)
    if not bbox:
        return
    x, y, width, height = bbox
    col_index = int(col_id.replace("#", "")) - 1
    cell_val = tree.item(row_id, "values")[col_index]
    label = tk.Label(tree, text=cell_val, bg="darkblue", fg="white", bd=0)
    label.place(x=x, y=y, width=width, height=height)
    tree.current_cell_highlight = label

# --- Event Handlers ---

def on_single_click(event, tree, database, text):
    # Sync any changes from detailed info.
    sync_detailed_info(text, tree, database)
    if tree.editing:
        return
    row_id = tree.identify_row(event.y)
    col_id = tree.identify_column(event.x)
    if row_id:
        update_detailed_preview(row_id, tree, database, text)
        update_row_highlight(tree, row_id)
        update_cell_highlight(tree, row_id, col_id)

def delayed_single_click(event, tree, database, text):
    if tree.editing:
        return
    if tree.single_click_after_id:
        tree.after_cancel(tree.single_click_after_id)
    tree.single_click_after_id = tree.after(100, lambda: on_single_click(event, tree, database, text))

def on_double_click(event, tree, database, text):
    if tree.single_click_after_id:
        tree.after_cancel(tree.single_click_after_id)
        tree.single_click_after_id = None
    if tree.editing:
        return
    row_id = tree.identify_row(event.y)
    col_id = tree.identify_column(event.x)
    if not row_id:
        return
    col_index = int(col_id.replace("#", "")) - 1
    # Only allow inline editing for "Quantity" (column 5) and "Location" (column 7)
    if col_index not in (4, 6):
        return
    if hasattr(tree, "current_cell_highlight") and tree.current_cell_highlight:
        tree.current_cell_highlight.destroy()
        tree.current_cell_highlight = None
    start_inline_edit(row_id, col_id, tree, database)

def start_inline_edit(row_id, col_id, tree, database):
    tree.editing = True
    bbox = tree.bbox(row_id, col_id)
    if not bbox:
        tree.editing = False
        return
    x, y, width, height = bbox
    col_index = int(col_id.replace("#", "")) - 1
    current_val = tree.item(row_id, "values")[col_index]
    entry = tk.Entry(tree)
    entry.insert(0, current_val)
    entry.place(x=x, y=y, width=width, height=height)
    entry.focus_set()
    entry.bind("<Return>", lambda e: finish_inline_edit(e, row_id, col_id, entry, tree, database))
    entry.bind("<FocusOut>", lambda e: finish_inline_edit(e, row_id, col_id, entry, tree, database))
    tree.editing_entry = entry

def finish_inline_edit(event, row_id, col_id, entry, tree, database):
    new_val = entry.get()
    entry.destroy()
    tree.editing_entry = None
    tree.editing = False
    col_index = int(col_id.replace("#", "")) - 1
    values = list(tree.item(row_id, "values"))
    values[col_index] = new_val
    tree.item(row_id, values=values)
    # Update the corresponding card using its unique ID.
    card_id = row_id
    for card in database:
        if card.get("ID") == card_id:
            if col_index == 4:  # Quantity column
                try:
                    card.setdefault("Inventory", {})["Current Quantity"] = int(new_val)
                except ValueError:
                    card.setdefault("Inventory", {})["Current Quantity"] = 0
            elif col_index == 6:  # Location column
                card.setdefault("Inventory", {})["Location"] = new_val
            break
    update_cell_highlight(tree, row_id, col_id)

def delete_current_card(tree, database, text):
    """Delete the currently selected card from both the treeview and database."""
    if not tree.selected_row:
        print("No row selected for deletion.")
        return
    card_id = tree.selected_row  # The unique ID is the tree item's id.
    for i, card in enumerate(database):
        if card.get("ID") == card_id:
            del database[i]
            break
    tree.delete(tree.selected_row)
    if card_id in tree.row_by_id:
        del tree.row_by_id[card_id]
    tree.selected_row = None
    text.delete("1.0", tk.END)
    print(f"Deleted card with ID '{card_id}'.")

def add_card(tree, database, text):
    default_card = {
        "Name": "",
        "Game": "YuGiOh",
        "Rarity": "Platinum Secret Rare",
        "Set Code": "RA03",
        "Inventory": {
            "Current Quantity": 1,
            "Target Quantity": 0,
            "Average Paid Price": 0,
            "Location": "M9",
            "Holding Period": "Long Term",
        },
        "Sales": {
            "Lifetime Sold": 0,
            "Last Sale Date": "",
            "Average Price Sold": 0
        },
        "Metadata": {
            "Card Type": "Monster",
            "Archetype": [""],
            "Synergy": [""],
            "Mechanics of Interaction": [""]
        }
    }
    # Assign a new unique ID.
    default_card["ID"] = get_next_unique_id(database)
    database.append(default_card)
    row_id = tree.insert("", "end", iid=default_card["ID"], values=treeview_values(default_card))
    tree.row_by_id[default_card["ID"]] = row_id
    update_row_highlight(tree, row_id)
    update_detailed_preview(row_id, tree, database, text)
    text.focus_set()

# --- New Functions: Move to Next/Previous Row on Tab ---

def move_to_next_row(event):
    """
    When Tab is pressed in the JSON preview, save any changes, then:
    - If there is a next row, select it.
    - If not, add a new row.
    Then, update the preview and set the cursor inside the "Name" field.
    Prevent the default Tab behavior.
    """
    text = event.widget
    tree = text.tree
    database = text.database

    sync_detailed_info(text, tree, database)

    children = list(tree.get_children())
    current_id = getattr(text, "current_card_id", None)
    if current_id not in children:
        if children:
            current_id = children[0]
        else:
            add_card(tree, database, text)
            children = list(tree.get_children())
            current_id = children[0]

    index = children.index(current_id)
    if index < len(children) - 1:
        next_id = children[index + 1]
    else:
        add_card(tree, database, text)
        children = list(tree.get_children())
        next_id = children[-1]

    update_detailed_preview(next_id, tree, database, text)
    update_row_highlight(tree, next_id)
    update_cell_highlight(tree, next_id, "#1")
    
    search_str = '"Name": "'
    pos = text.search(search_str, "1.0", stopindex="end")
    if pos:
        new_index = f"{pos}+{len(search_str)}c"
        text.mark_set("insert", new_index)
        text.see("insert")
    return "break"

def move_to_previous_row(event):
    """
    When Shift+Tab is pressed in the JSON preview, save any changes, then:
    - If there is a previous row, select it.
    - If already at the first row, remain there.
    Then, update the preview and set the cursor inside the "Name" field.
    Prevent the default Shift+Tab behavior.
    """
    text = event.widget
    tree = text.tree
    database = text.database

    sync_detailed_info(text, tree, database)

    children = list(tree.get_children())
    current_id = getattr(text, "current_card_id", None)
    if current_id not in children:
        if children:
            current_id = children[0]
        else:
            # If no rows exist, add one.
            add_card(tree, database, text)
            children = list(tree.get_children())
            current_id = children[0]

    index = children.index(current_id)
    if index > 0:
        prev_id = children[index - 1]
    else:
        prev_id = children[0]  # Already at the top; remain there.

    update_detailed_preview(prev_id, tree, database, text)
    update_row_highlight(tree, prev_id)
    update_cell_highlight(tree, prev_id, "#1")
    
    search_str = '"Name": "'
    pos = text.search(search_str, "1.0", stopindex="end")
    if pos:
        new_index = f"{pos}+{len(search_str)}c"
        text.mark_set("insert", new_index)
        text.see("insert")
    return "break"

# --- Main GUI Creation ---

def create_inventory_gui():
    root = tk.Tk()
    root.title("Inventory Manager")
    root.geometry("1920x1080")

    title = tk.Label(root, text="Card Inventory", font=("Arial", 14, "bold"))
    title.pack(pady=10)

    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Left: Treeview (spreadsheet)
    left_frame = tk.Frame(main_frame, width=1536, height=1080)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    columns = ("Name", "Game", "Rarity", "Set Code", "Quantity", "Avg Paid", "Location")
    tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="none")
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
    style.configure("Treeview", rowheight=25)
    tree.tag_configure("row_light_blue", background="lightblue")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill=tk.BOTH, expand=True)

    tree.single_click_after_id = None
    tree.current_cell_highlight = None
    tree.editing_entry = None
    tree.selected_row = None
    tree.editing = False

    database = load_database()
    populate_table(tree, database)

    # Right: Detailed Card Info (raw JSON) with undo enabled.
    right_frame = tk.Frame(main_frame, width=384, height=1080)
    right_frame.pack(side=tk.RIGHT, fill=tk.Y, anchor="n")
    preview_label = tk.Label(right_frame, text="Detailed Card Info", font=("Arial", 12, "bold"))
    preview_label.pack(pady=10)
    text = tk.Text(right_frame, wrap=tk.WORD, height=40, width=50, undo=True)
    text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    text.edit_modified(False)
    # Attach references for use in Tab handlers.
    text.tree = tree
    text.database = database

    # Bind events.
    text.bind("<FocusOut>", lambda e: sync_detailed_info(text, tree, database))
    tree.bind("<ButtonRelease-1>", lambda e: delayed_single_click(e, tree, database, text))
    tree.bind("<Double-ButtonRelease-1>", lambda e: on_double_click(e, tree, database, text))
    text.bind("<Tab>", move_to_next_row)
    text.bind("<Shift-Tab>", move_to_previous_row)

    # Bottom buttons.
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    add_btn = ttk.Button(btn_frame, text="Add Card", command=lambda: add_card(tree, database, text))
    save_btn = ttk.Button(btn_frame, text="Save", command=lambda: save_database(database))
    delete_btn = ttk.Button(btn_frame, text="Delete Card", command=lambda: delete_current_card(tree, database, text))
    add_btn.grid(row=0, column=0, padx=5)
    save_btn.grid(row=0, column=1, padx=5)
    delete_btn.grid(row=0, column=2, padx=5)

    root.mainloop()

if __name__ == "__main__":
    create_inventory_gui()
