import os
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, quote_plus
from db_mongo import get_next_topic, store_post
from gmail_utils import send_approval_email
from pyngrok import ngrok

API_KEY = "AIzaSyA4Scmt285IARpxf60yfNwadj_YX47rDGg"
CX = "243a912605e024b27"
HF_API_TOKEN = "HF_TOKEN_REDACTED"
HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
NGROK_AUTH_TOKEN = "2ztUSHj7MQ5CrCwQALsE7uHVrQv_6KE2ZX9wvdNCPWrdjpb7b"
BLOCKED_DOMAINS = [
    "reddit.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "imdb.com",
]

if NGROK_AUTH_TOKEN:
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)


def search_urls_google(query, max_results=15):
    print(f"[INFO] Searching Google for top {max_results} URLs for: '{query}'")
    urls = []
    start = 1
    while len(urls) < max_results and start < 50:
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}&start={start}"
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            for item in items:
                link = item.get("link")
                if not link or any(domain in link for domain in BLOCKED_DOMAINS):
                    continue
                if link not in urls:
                    urls.append(link)
                if len(urls) >= max_results:
                    break
            start += 10
        except Exception as e:
            print(f"[SEARCH ERROR] {e}")
            break
    print(f"[SEARCH] Found {len(urls)} URLs.")
    return urls


def scrape_and_combine_content(urls, max_to_scrape=5):
    print(f"[SCRAPER] Attempting to scrape up to {max_to_scrape} valid articles...")
    all_text = ""
    scraped_count = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for url in urls:
            if scraped_count >= max_to_scrape:
                break
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")
                main = soup.find("article") or soup.find("main") or soup.body
                content = main.get_text(separator="\n", strip=True) if main else ""
                if not content or len(content.split()) < 150:
                    continue
                all_text += f"--- Content from {url} ---\n\n{content}\n\n"
                scraped_count += 1
                print(f"[SCRAPED] Successfully scraped content from {url}")
            except Exception as e:
                print(f"[ERROR] Could not scrape {url}: {e}")
        browser.close()
    return all_text


def generate_combined_post_with_ollama(all_content, topic):
    print("[OLLAMA] Generating LinkedIn post...")
    prompt = f'Based on these articles about "{topic}", write a concise, engaging LinkedIn post. Synthesize key insights. End with 3-5 relevant hashtags.\n\nARTICLES:\n{all_content[:8000]}'
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=300,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"[OLLAMA ERROR] {e}")
        return None


def generate_image_from_post(post_text, topic):
    print("[IMAGE] Generating image from Hugging Face...")
    style_prompt = "an artistic and visually stunning image, cinematic photo, high detail, masterpiece, 8k, professional, no text"
    final_prompt = f"{post_text[:350]}, {style_prompt}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": final_prompt}
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        image_bytes = response.content
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " _-").rstrip()
        output_path = f"output_{safe_topic[:20]}.png"
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f"[IMAGE SAVED] Image saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"[IMAGE ERROR] Failed to generate image: {e}")
        return None


def get_ngrok_public_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        response.raise_for_status()
        tunnels = response.json().get("tunnels", [])
        if tunnels:
            https_tunnel = next((t for t in tunnels if t.get("proto") == "https"), None)
            if https_tunnel:
                return https_tunnel.get("public_url")
        return None
    except requests.exceptions.ConnectionError:
        print(
            "[ERROR] Could not connect to ngrok agent. Is 'run_approval_server.py' running?"
        )
        return None


def process_one_topic():
    """
    Processes a single topic from the queue and sends it for approval.
    """
    topic = get_next_topic()
    if not topic:
        print("[INFO] All topics have been processed. Nothing to do.")
        return

    print("\n" + "=" * 60)
    print(f"[START] Processing topic: '{topic}' at {datetime.now().isoformat()}")

    try:
        # NOTE: The delete_all_articles() call has been removed as requested.

        urls = search_urls_google(topic)
        if not urls:
            raise ValueError(f"No URLs found for topic '{topic}'.")

        combined_text = scrape_and_combine_content(urls)
        if not combined_text:
            raise ValueError(f"No valid content could be scraped for topic '{topic}'.")

        post_text = generate_combined_post_with_ollama(combined_text, topic)
        image_path = generate_image_from_post(post_text, topic) if post_text else None

        if not post_text or not image_path:
            raise ValueError("Post or image generation failed.")

        public_url = get_ngrok_public_url()
        if not public_url:
            raise ConnectionError(
                "Could not get ngrok URL. Ensure approval server is running."
            )

        # Store post with 'pending_approval' status
        post_id = store_post(
            {
                "topic": topic,
                "generated_post": post_text,
                "generated_image_path": image_path,
                "status": "pending_approval",
                "created_at": datetime.utcnow(),
            }
        )
        print(f"[DB] Stored pending post with ID: {post_id}")

        # --- NEW: Construct links with the topic as a query parameter ---
        encoded_topic = quote_plus(topic)  # Safely encode the topic for the URL
        approve_link = f"{public_url}/approve/{post_id}?topic={encoded_topic}"
        reject_link = f"{public_url}/reject/{post_id}?topic={encoded_topic}"

        send_approval_email(
            to="jishnuparuchuri8888@gmail.com",
            subject=f"Action Required: Review Post on '{topic}'",
            post_text=post_text,
            image_path=image_path,
            approve_link=approve_link,
            reject_link=reject_link,
        )

        print(f"[SUCCESS] Topic '{topic}' processed and sent for approval.")

    except Exception as e:
        print(
            f"[WORKFLOW ERROR] A failure occurred while processing topic '{topic}': {e}"
        )

    # NOTE: The mark_topic_scraped() call in a 'finally' block is removed.
    # The topic status will only be updated upon approval/rejection.

    print(f"[DONE] Topic processing for '{topic}' is complete. Awaiting approval.")
    print("=" * 60 + "\n")
