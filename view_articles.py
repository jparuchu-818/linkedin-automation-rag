from pymongo import MongoClient
from pprint import pprint

client = MongoClient("mongodb://localhost:27017/")
db = client.linkedin_bot

latest_articles = db.articles.find().sort("scraped_at", -1).limit(5)

for doc in latest_articles:
    print("\n" + "="*80)
    print(f"Topic: {doc['topic']}")
    print(f"URL: {doc['url']}")
    print("-" * 80)
    print("TEXT:")
    print(doc['content'][:1000]) # Keep it short for display
    print("-" * 80)
    
    if 'images' in doc and doc['images']:
        print(f"IMAGES ({len(doc['images'])} found):")
        # Print the first 5 image URLs
        for img_url in doc['images'][:5]:
            print(f"  - {img_url}")
    else:
        print("IMAGES: None found.")