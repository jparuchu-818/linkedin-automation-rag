import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

from django.core.management.base import BaseCommand
from pipeline.models import Topic, Post  # Import Django models
from django.utils import timezone


from gmail_utils import send_approval_email
# Your existing helper functions for scraping and generation
# NOTE: We are moving them inside this command file.
# You will also need to add your API keys here or preferably in Django's settings.py

# --- API KEYS AND CONFIGURATION ---
API_KEY = "AIzaSyA4Scmt285IARpxf60yfNwadj_YX47rDGg"
CX = "243a912605e024b27"
HF_API_TOKEN = "HF_TOKEN_REDACTED"
HF_MODEL = "CompVis/stable-diffusion-v1-4"
BLOCKED_DOMAINS = ['reddit.com', 'facebook.com']

def search_urls_google(query, max_results=15):
    # ... (This function is the same as before)
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
                if not link or any(domain in link for domain in BLOCKED_DOMAINS): continue
                if link not in urls: urls.append(link)
                if len(urls) >= max_results: break
            start += 10
        except Exception as e:
            print(f"[SEARCH ERROR] {e}")
            break
    print(f"[SEARCH] Found {len(urls)} URLs.")
    return urls

def scrape_and_combine_content(urls, max_to_scrape=5):
    # This requires Playwright, make sure it's installed in your environment
    from playwright.sync_api import sync_playwright
    print(f"[SCRAPER] Scraping up to {max_to_scrape} valid articles...")
    all_text = ""
    # ... (rest of the function is the same as before)
    scraped_count = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for url in urls:
            if scraped_count >= max_to_scrape: break
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=20000)
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                main = soup.find('article') or soup.find('main') or soup.body
                content = main.get_text(separator='\n', strip=True) if main else ""
                if not content or len(content.split()) < 150: continue
                all_text += f"--- Content from {url} ---\n\n{content}\n\n"
                scraped_count += 1
                print(f"[SCRAPED] Successfully scraped {url}")
            except Exception as e:
                print(f"[ERROR] Could not scrape {url}: {e}")
        browser.close()
    return all_text


def generate_combined_post_with_ollama(all_content, topic):
    # ... (This function is the same as before)
    print("[OLLAMA] Generating LinkedIn post...")
    prompt = f'Based on these articles about "{topic}", write a concise, engaging LinkedIn post. Synthesize key insights. End with 3-5 relevant hashtags.\n\nARTICLES:\n{all_content[:8000]}'
    try:
        response = requests.post("http://localhost:11434/api/generate", json={"model": "llama3", "prompt": prompt, "stream": False}, timeout=300)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"[OLLAMA ERROR] {e}")
        return None

def generate_image_from_post(post_text, topic):
    # ... (This function is the same as before)
    print("[IMAGE] Generating image...")
    style_prompt = "an artistic and visually stunning image, cinematic photo, high detail"
    final_prompt = f"{post_text[:350]}, {style_prompt}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": final_prompt}
    try:
        response = requests.post(f"https://api-inference.huggingface.co/models/{HF_MODEL}", headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        image_bytes = response.content
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " _-").rstrip()
        output_path = f"output_{safe_topic[:20]}.png"
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f"[IMAGE SAVED] {output_path}")
        return output_path
    except Exception as e:
        print(f"[IMAGE ERROR] {e}")
        return None

# This is the required structure for a Django management command
class Command(BaseCommand):
    help = 'Runs the full content generation pipeline for one pending topic.'

    def handle(self, *args, **options):
        """
        The main logic for the management command.
        """
        
        # 1. Get next topic using the Django ORM
        self.stdout.write(self.style.SUCCESS("[INFO] Finding next topic with status 'pending'..."))
        topic_obj = Topic.objects.filter(status='pending').first()

        if not topic_obj:
            self.stdout.write(self.style.SUCCESS("[INFO] All topics have been processed. Nothing to do."))
            return

        topic_name = topic_obj.name
        self.stdout.write(self.style.SUCCESS(f"\n[START] Processing topic: '{topic_name}'"))

        try:
            # 2. Search, Scrape, and Generate AI Content
            urls = search_urls_google(topic_name)
            if not urls:
                raise ValueError("No URLs found from Google Search.")

            combined_text = scrape_and_combine_content(urls)
            if not combined_text:
                raise ValueError("Could not scrape any valid content from URLs.")
            
            post_text = generate_combined_post_with_ollama(combined_text, topic_name)
            image_path = generate_image_from_post(post_text, topic_name) if post_text else None

            if not post_text or not image_path:
                raise ValueError("AI content or image generation failed.")

            # 3. Store the final post in the database
            post_obj = Post.objects.create(
                topic=topic_obj,
                generated_post=post_text,
                generated_image_path=image_path,
                status='pending_approval'
            )
            self.stdout.write(self.style.SUCCESS(f"[DB] Stored pending post with ID: {post_obj.id}"))
            
            # 4. Create approval links and send the email
            # NOTE: For testing, this uses your local Django server address.
            # In production, this would be your public domain name.
            base_url = "http://127.0.0.1:8000"
            approve_link = f"{base_url}/approve/{post_obj.id}/"
            reject_link = f"{base_url}/reject/{post_obj.id}/"
            
            send_approval_email(
                to="jishnuparuchuri8888@gmail.com", # Or your desired review email
                subject=f"Action Required: Review Post on '{topic_name}'",
                post_text=post_text,
                image_path=image_path,
                approve_link=approve_link,
                reject_link=reject_link
            )
            
            # 5. Update the topic's status to prevent reprocessing
            topic_obj.status = 'awaiting_approval'
            topic_obj.processed_at = timezone.now()
            topic_obj.save()
            self.stdout.write(self.style.SUCCESS(f"[SUCCESS] Topic '{topic_name}' processed and is now awaiting approval."))

        except Exception as e:
            # If any step fails, log the error. The topic status remains 'pending'
            # so it can be attempted again on the next run.
            self.stderr.write(self.style.ERROR(f"[WORKFLOW ERROR] A failure occurred while processing '{topic_name}': {e}"))