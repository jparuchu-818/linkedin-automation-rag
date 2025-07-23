from db_mongo import find_one_approved_post, update_post_status_to_published
from linkedin_utils import linkedin_authenticate
from linkedin_post import get_author_urn, post_text_to_linkedin


def publish_one_post():
    """
    Main orchestrator for the publishing workflow. Finds one approved post,
    publishes it to LinkedIn, and updates its status in the database.
    """
    print("--- Starting Publisher ---")

    print("Step 1: Checking database for an 'approved' post...")
    approved_post = find_one_approved_post()

    if not approved_post:
        print("No approved posts found. Nothing to do.")
        print("--- Publisher Finished ---")
        return

    print(f"Found post for topic: '{approved_post['topic']}'")

    print("Step 2: Authenticating with LinkedIn...")
    credentials = linkedin_authenticate()

    if not credentials or not credentials.token:
        print("LinkedIn authentication failed. Could not get access token. Exiting.")
        print("--- Publisher Finished ---")
        return

    print("Step 3: Getting access token and author URN...")
    access_token = credentials.token
    author_urn = get_author_urn(access_token)

    if not author_urn:
        print("Could not retrieve author URN. Exiting.")
        print("--- Publisher Finished ---")
        return

    print("Step 4: Sending content to LinkedIn API...")
    post_text = approved_post["generated_post"]
    success = post_text_to_linkedin(access_token, author_urn, post_text)

    if success:
        print("Step 5: Updating post status in database to 'published'...")
        post_id = approved_post["_id"]
        update_post_status_to_published(post_id)
    else:
        print("Step 5: Skipping database update due to posting failure.")

    print("--- Publisher Finished ---")


if __name__ == "__main__":
    publish_one_post()
