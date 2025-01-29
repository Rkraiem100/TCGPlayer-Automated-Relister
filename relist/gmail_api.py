#gmail_api.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import json
import re
from datetime import datetime
import base64
import time
from bs4 import BeautifulSoup


# Configuration
DEBUG = True  # Detailed console output
MAX_EMAILS_TO_LIST = 100  # Number of email IDs to fetch in list() call
TRACKED_CARDS = ["Arcane Signet", "Snake Rain", "Haggard Lizardose", "Escape Tunnel"]
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Store message IDs in memory
stored_message_ids = set()

def debug_print(message):
    """Print debug messages if DEBUG is enabled."""
    if DEBUG:
        print(f"[DEBUG] {message}")

def load_or_create_json():
    """Load existing JSON file or create a new one if it doesn't exist."""
    json_path = os.path.join(os.path.dirname(__file__), 'orders.json')
    global stored_message_ids
    
    if os.path.exists(json_path):
        debug_print("Loading existing orders database.")
        with open(json_path, 'r') as file:
            data = json.load(file)
            if 'recent_message_ids' not in data:
                data['recent_message_ids'] = []
            stored_message_ids = set(data['recent_message_ids'])
            debug_print(f"Loaded {len(stored_message_ids)} most recent message IDs")
            return data
    else:
        debug_print("Creating new orders database.")
        initial_data = {
            "processed_orders": [],
            "last_check_time": None,
            "total_tracked_sales": {card: 0 for card in TRACKED_CARDS},
            "recent_message_ids": []
        }
        with open(json_path, 'w') as file:
            json.dump(initial_data, file, indent=4)
        return initial_data

def save_json(data):
    """Save data to JSON file."""
    json_path = os.path.join(os.path.dirname(__file__), 'orders.json')
    try:
        with open(json_path, 'w') as file:
            json.dump(data, file, indent=4)
            debug_print("Successfully saved to JSON file")
    except Exception as e:
        print(f"Error saving JSON: {e}")

def connect_to_gmail_api():
    """Connects to the Gmail API and returns a service object."""
    creds = None
    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    
    try:
        if os.path.exists(token_path):  # Changed from 'token.json'
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)  # Use full path
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:  # Use full path
                token.write(creds.to_json())
                
        service = build('gmail', 'v1', credentials=creds)
        print("Gmail API connected successfully!")
        return service
        
    except Exception as e:
        print(f"Error connecting to Gmail API: {e}")
        print(f"Looking for credentials at: {credentials_path}")
        print(f"Looking for/saving token at: {token_path}")
        return None

def extract_order_info(message):
    """Extract order ID and tracked card quantities from email message."""
    try:
        data = None
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/html':
                    data = part['body'].get('data')
                    break
        else:
            data = message['payload']['body'].get('data')

        if data:
            html = base64.urlsafe_b64decode(data).decode()
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()

            order_match = re.search(r'Order:\s*([A-F0-9]{8}-[A-F0-9]{6}-[A-F0-9]{5})', text)
            order_id = order_match.group(1) if order_match else None

            card_sales = {}
            for card in TRACKED_CARDS:
                card_pattern = rf'(\d+)\s+{re.escape(card)}/Near Mint'
                matches = re.finditer(card_pattern, text)
                total_quantity = sum(int(match.group(1)) for match in matches)
                if total_quantity > 0:
                    card_sales[card] = total_quantity
                    debug_print(f"Found {total_quantity}x {card}")

            return order_id, card_sales

    except Exception as e:
        print(f"Error extracting information: {e}")
        return None, {}

def get_new_message_ids(service, order_data):
    """Get list of message IDs and identify new ones."""
    try:
        debug_print("Fetching recent TCGPlayer sales emails...")
        query = 'from:sales@tcgplayer.com subject:"Your TCGplayer.com items of "'
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=MAX_EMAILS_TO_LIST
        ).execute()
        
        messages = results.get('messages', [])
        current_ids = [msg['id'] for msg in messages]
        
        if not stored_message_ids:  # First run
            new_ids = current_ids
            debug_print("First run - processing all available messages")
        else:
            # Find the index of the most recent stored ID in current list
            bookmark_index = None
            for id in stored_message_ids:
                try:
                    index = current_ids.index(id)
                    if bookmark_index is None or index < bookmark_index:
                        bookmark_index = index
                except ValueError:
                    continue
            
            if bookmark_index is not None:
                # Only process messages newer than our bookmark
                new_ids = current_ids[:bookmark_index]
                debug_print(f"Found {len(new_ids)} new messages since last check")
            else:
                new_ids = current_ids
                debug_print("No stored IDs found in recent messages - processing all")
        
        # Update stored IDs with most recent ones
        order_data['recent_message_ids'] = current_ids[:10]
        save_json(order_data)
        
        return new_ids
        
    except Exception as e:
        print(f"Error getting message IDs: {e}")
        return []

def process_emails(service):
    """Process new emails and return tracked card sales or None if no sales are found."""
    try:
        debug_print("Starting email processing...")
        order_data = load_or_create_json()
        
        new_message_ids = get_new_message_ids(service, order_data)
        
        if not new_message_ids:
            debug_print("No new messages to process")
            return None  # Return None when there are no new messages
        
        messages_processed = 0
        all_card_sales = {}  # To aggregate sales data across all emails
        
        for message_id in new_message_ids:
            try:
                # Skip already processed messages
                if any(order['email_id'] == message_id for order in order_data['processed_orders']):
                    continue
                
                message = service.users().messages().get(userId='me', id=message_id).execute()
                order_id, card_sales = extract_order_info(message)
                
                # Aggregate card sales
                for card, quantity in card_sales.items():
                    all_card_sales[card] = all_card_sales.get(card, 0) + quantity
                
                new_order = {
                    "email_id": message_id,
                    "order_id": order_id if order_id else "UNKNOWN_ORDER_ID",
                    "timestamp": datetime.now().isoformat(),
                    "needs_review": order_id is None,
                    "tracked_cards": card_sales
                }
                
                order_data['processed_orders'].append(new_order)
                for card, quantity in card_sales.items():
                    order_data['total_tracked_sales'][card] += quantity
                
                if card_sales:
                    debug_print(f"Processed order {order_id}: {card_sales}")
                messages_processed += 1
                
            except Exception as e:
                print(f"Error processing message {message_id}: {e}")
                continue
        
        order_data['last_check_time'] = datetime.now().isoformat()
        save_json(order_data)
        print(f"Successfully processed {messages_processed} new messages")
        
        # Return aggregated card sales if any, otherwise return None
        return all_card_sales if all_card_sales else None
    
    except Exception as e:
        print(f"Error in process_emails: {e}")
        return None


def fetch_tcgplayer_email(service):
    """
    Main function to fetch and process emails. 
    Returns a dictionary of tracked card sales or None if no sales are found.
    """
    debug_print("Starting email processing")
    result = process_emails(service)
    debug_print("Email processing complete")
    return result


if __name__ == "__main__":
    service = connect_to_gmail_api()
    if service:
        fetch_tcgplayer_email(service)