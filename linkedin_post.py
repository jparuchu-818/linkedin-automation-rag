import requests
import json


def get_author_urn(access_token: str) -> str | None:
    """
    Gets the authenticated user's unique LinkedIn ID (URN) using their access token.
    This is required to specify who is making the post.
    """
    print("[INFO] Fetching author's URN from LinkedIn API...")
    url = "https://api.linkedin.com/v2/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        author_urn = data.get("id")
        if not author_urn:
            print("[ERROR] Could not find 'id' (URN) in the API response.")
            return None

        print(f"[SUCCESS] Found Author URN: {author_urn}")
        return author_urn

    except Exception as e:
        print(f"[API ERROR] Could not retrieve LinkedIn URN: {e}")
        return None


def post_text_to_linkedin(access_token: str, author_urn: str, post_text: str) -> bool:
    """
    Posts a text update to LinkedIn on behalf of the authenticated user.
    Uses the /v2/ugcPosts endpoint.
    """
    print("[INFO] Preparing to post content to LinkedIn via ugcPosts endpoint...")
    url = "https://api.linkedin.com/v2/ugcPosts"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # This is the specific JSON structure required by the ugcPosts API
    payload = {
        "author": f"urn:li:person:{author_urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": post_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        post_id = response.json().get("id")
        print(f"[SUCCESS] Successfully posted to LinkedIn. Post ID: {post_id}")
        return True

    except Exception as e:
        print(f"[API ERROR] Failed to post to LinkedIn: {e}")
        return False
