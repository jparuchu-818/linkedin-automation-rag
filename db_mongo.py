# db_mongo.py

from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

# --- Database Connection ---
client = MongoClient("mongodb://localhost:27017/")
db = client["linkedin_bot"]
topics_collection = db["topics"]
posts_collection = db["posts"]


def get_next_topic():
    """Finds the first topic with the status 'pending'."""
    # We now look for status 'pending' instead of a 'scraped' flag
    topic_doc = topics_collection.find_one({"status": "pending"})
    return topic_doc["topic"] if topic_doc else None


def mark_topic_as_processed(topic_name: str):
    """
    Finds a topic by its name and updates its status to 'processed'.
    This will be called by the approval server.
    """
    if topic_name:
        topics_collection.update_one(
            {"topic": topic_name},
            {"$set": {"status": "processed", "processed_at": datetime.utcnow()}},
        )
        print(f"[DB] Marked topic '{topic_name}' as processed.")


def delete_all_articles():
    # This function remains but we will stop calling it from the main script.
    result = posts_collection.delete_many({})
    print(f"[DB] Deleted {result.deleted_count} old posts.")
    return result.deleted_count


def store_post(post_data: dict) -> ObjectId:
    """Stores a single post document and returns its unique ID."""
    result = posts_collection.insert_one(post_data)
    return result.inserted_id


def update_post_status(post_id: str, status: str):
    """Finds a post by its ID and updates its status."""
    result = posts_collection.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}},
    )
    if result.matched_count > 0:
        print(f"[DB] Updated post {post_id} to status: '{status}'")
    else:
        print(f"[DB ERROR] Could not find post with ID {post_id} to update.")
