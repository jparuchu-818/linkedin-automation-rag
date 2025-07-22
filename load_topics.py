from db_mongo import topics
from datetime import datetime

initial_topics = [
    "best dribblers in football in 21st century",
    "Movies with unforgettable one-liners",
    "Foreign films everyone should watch",
    "Underrated movies of the last 10 years",
    "Movies with the best soundtracks of all time",
    "Cult classic films that flopped initially",
    "Oscar-nominated films that lost",
    "Hidden gems from the 90s",
    "Movies with open endings",
    "Movies based on true stories",
    "Best animated movies for adults"
]

for topic in initial_topics:
    topics.insert_one({
        "topic": topic,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "processed_at": None
    })

print(f"[INFO] Inserted {len(initial_topics)} topics.")
