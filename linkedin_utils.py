import os
import json
import webbrowser
from requests_oauthlib import OAuth2Session

CLIENT_ID = ""
CLIENT_SECRET = ""

REDIRECT_URI = "https://localhost/callback"
SCOPES = ["r_liteprofile", "w_member_social"]
TOKEN_FILE = "linkedin_token.json"

# linkedin api urls
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"


def linkedin_authenticate():
    
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token = json.load(f)
    else:
        token = None

    if token:
        print("Found saved token, creating session.")
        sess = OAuth2Session(CLIENT_ID, token=token, auto_refresh_url=TOKEN_URL,
                                         auto_refresh_kwargs={'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET},
                                         token_updater=lambda t: save_token(t)) 
        return sess

    print("No token file found, starting new login flow.")
    
    sess = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
    auth_url = sess.authorization_url(AUTH_URL)

    print("Opening browser for authentication...")
    webbrowser.open(auth_url)

    redirect_resp = input("\nPaste the full redirect URL here:\n> ")

    try:
        new_token = sess.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            authorization_response=redirect_resp
        )
        # save it for next time
        with open(TOKEN_FILE, "w") as f:
            json.dump(new_token, f)
        print("Token fetched and saved.")
        return sess
    except Exception as e:
        print(f"Error fetching token: {e}")
        return None

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f)
    print("Token was refreshed and saved.")