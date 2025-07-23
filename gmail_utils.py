import os
import base64
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Optional, Dict

# --- Google API Imports ---
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

# Gmail API scope for sending emails
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def load_credentials():
    """Load credentials from token.json if they exist and are valid."""
    if os.path.exists("token.json"):
        credents = Credentials.from_authorized_user_file("token.json", SCOPES)
        if credents and credents.valid:
            return credents
    return None


def refresh_credentials(credents):
    """Attempt to refresh expired credentials."""
    try:
        credents.refresh(Request())
        return credents
    except Exception as e:
        print(f"[AUTH] Failed to refresh token: {e}")
        return None


def create_new_credentials():
    """Run OAuth flow to get new credentials."""
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    credents = flow.run_local_server(port=0)
    return credents


def gmail_authenticate():
    """
    Authenticate and return Gmail API service.
    Loads from token, refreshes, or initiates new OAuth flow as needed.
    """
    credents = load_credentials()

    if credents and credents.expired and credents.refresh_token:
        credents = refresh_credentials(credents)

    if not credents or not credents.valid:
        credents = create_new_credentials()

    with open("token.json", "w") as token_file:
        token_file.write(credents.to_json())

    return build("gmail", "v1", credentials=credents)


def _create_message_with_link(
    to: str, subject: str, post_text: str, image_path: str, approval_link: str
) -> Dict[str, str]:
    """
    Creates a MIME message with an HTML body containing a clickable approval link.
    """
    msg = MIMEMultipart("related")  # 'related' is best for emails with embedded content
    msg["To"] = to
    msg["Subject"] = subject

    # --- Create the HTML part of the email ---
    # This HTML includes a styled button for the approval link
    html_body = f"""
    <html>
    <head>
      <style>
        .button {{
          background-color: #4CAF50; color: white; padding: 15px 25px;
          text-align: center; text-decoration: none; display: inline-block;
          font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 8px;
        }}
      </style>
    </head>
    <body>
      <p>Hello,</p>
      <p>Please review the following generated content for LinkedIn.</p>
      <a href="{approval_link}" class="button">Click Here to Approve Post</a>
      <hr>
      <h3>Post Preview:</h3>
      <pre style="white-space: pre-wrap; font-family: sans-serif;">{post_text}</pre>
      <hr>
      <p>The generated image is attached.</p>
      <p>Thank you,<br></p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html"))

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img = MIMEImage(f.read())
        img.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(image_path)
        )
        msg.attach(img)
        print(f"[EMAIL] Attached image: {os.path.basename(image_path)}")

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw_message}


# In gmail_utils.py

# ... (all imports and the gmail_authenticate function remain the same)


def send_approval_email(
    to: str,
    subject: str,
    post_text: str,
    image_path: str,
    approve_link: str,
    reject_link: str,
):
    """
    Main function to send an approval email containing clickable Approve/Reject buttons.
    """
    service = gmail_authenticate()
    if not service:
        print("[EMAIL ERROR] Cannot send email due to authentication failure.")
        return

    # --- Create the HTML part of the email ---
    html_body = f"""
    <html>
    <head>
      <style>
        .button {{
          padding: 12px 25px; text-align: center; text-decoration: none;
          display: inline-block; font-size: 16px; margin: 10px 2px;
          cursor: pointer; border-radius: 8px; color: white; border: none;
        }}
        .approve-btn {{ background-color: #28a745; }} /* Green */
        .reject-btn {{ background-color: #dc3545; }} /* Red */
      </style>
    </head>
    <body>
      <p>Hello,</p>
      <p>Please review the following generated content for LinkedIn and choose an action:</p>
      <a href="{approve_link}" class="button approve-btn">Approve Post</a>
      <a href="{reject_link}" class="button reject-btn">Reject Post</a>
      <hr>
      <h3>Post Preview:</h3>
      <pre style="white-space: pre-wrap; font-family: sans-serif; padding: 1em; background-color: #f8f9fa; border-radius: 5px;">{post_text}</pre>
      <hr>
      <p>The generated image is attached.</p>
    </body>
    </html>
    """

    # Create the main email container
    msg = MIMEMultipart("related")
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    # Attach the image
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img = MIMEImage(f.read())
        img.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(image_path)
        )
        msg.attach(img)

    # Encode and send
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try:
        service.users().messages().send(
            userId="me", body={"raw": raw_message}
        ).execute()
        print(f"[EMAIL SUCCESS] Approval email sent to {to}.")
    except Exception as e:
        print(f"[EMAIL API ERROR] {e}")
