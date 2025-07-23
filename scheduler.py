from search_scrape import process_one_topic
from datetime import datetime

print(f"[SCHEDULER] Triggered at {datetime.now().isoformat()}")
process_one_topic()
