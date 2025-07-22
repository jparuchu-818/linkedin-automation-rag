import os
import base64
import time
from datetime import datetime, timedelta
from pymongo import MongoClient
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from db_mongo import update_post_status

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def gmail_authenticate():
    """Authenticate and return Gmail API service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_body(msg_data):
    """Parses the email payload to find the plain text body."""
    payload = msg_data.get("payload", {})
    parts = payload.get("parts", [])
    if parts:
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode().strip()
    elif "body" in payload and "data" in payload["body"]:
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode().strip()
    return ""

def check_for_approvals():
    """
    Checks for emails with 'APPROVED' in the body that are replies to our bot.
    """
    print("[INFO] Waiting 15 seconds for Gmail API to index new emails...")
    time.sleep(15)

    service = gmail_authenticate()
    if not service:
        print("[ERROR] Failed to authenticate with Gmail.")
        return
    
    query = 'subject:"Generated Post:" is:unread newer_than:1h'
    
    print(f"[INFO] Searching for approval emails with query: '{query}'")
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    if not messages:
        print("[INFO] No new approval emails found.")
        return

    print(f"[INFO] Found {len(messages)} potential approval email(s).")

    for msg_summary in messages:
        msg_id = msg_summary['id']
        msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        
        email_body = get_body(msg_data)
        
        if email_body and email_body.upper().strip().startswith("APPROVED"):
            print(f"[SUCCESS] Approval found in email ID: {msg_id}")
            update_post_status("approved")
            
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            print(f"[GMAIL] Marked email {msg_id} as read.")
            break 
    else:
        print("[INFO] No emails contained the 'APPROVED' keyword.")

if __name__ == "__main__":
    check_for_approvals()