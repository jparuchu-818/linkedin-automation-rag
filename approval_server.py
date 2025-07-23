# approval_server.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from bson.objectid import ObjectId
import uvicorn

# --- Import your new DB function ---
from db_mongo import update_post_status, mark_topic_as_processed

# --- Create the FastAPI app ---
app = FastAPI()


# --- HTML Templates for Responses (no changes here) ---
def create_html_response(message: str, color: str) -> str:
    # ... (this function remains the same)
    return f"""
    <html><head><title>Post Status</title><style>body{{display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif;background-color:#f0f2f5;}}.container{{text-align:center;padding:40px;border-radius:12px;background-color:white;box-shadow:0 4px 12px rgba(0,0,0,0.1);}}.status-icon{{font-size:48px;}}.message{{font-size:24px;color:#333;margin-top:20px;}}.status-approved{{color:{color};}}</style></head>
    <body><div class="container"><div class="status-icon status-approved">{'✅' if color == '#28a745' else '🗑️'}</div><div class="message">{message}</div></div></body></html>
    """


# --- MODIFIED: Endpoints now accept a 'topic' query parameter ---
@app.get("/approve/{post_id}", response_class=HTMLResponse)
def approve_post(post_id: str, topic: str):
    """Approves a post AND marks the parent topic as processed."""
    print(f"[SERVER] Received APPROVAL for post {post_id} on topic '{topic}'")
    try:
        update_post_status(post_id, "approved")
        mark_topic_as_processed(topic)  # <-- NEW: Update the topic status
        return create_html_response(
            f"Post for topic '{topic}' has been APPROVED.", "#28a745"
        )
    except Exception as e:
        return HTMLResponse(
            content=create_html_response(
                "An internal server error occurred.", "#dc3545"
            ),
            status_code=500,
        )


@app.get("/reject/{post_id}", response_class=HTMLResponse)
def reject_post(post_id: str, topic: str):
    """Rejects a post AND marks the parent topic as processed."""
    print(f"[SERVER] Received REJECTION for post {post_id} on topic '{topic}'")
    try:
        update_post_status(post_id, "rejected")
        mark_topic_as_processed(topic)  # <-- NEW: Update the topic status
        return create_html_response(
            f"Post for topic '{topic}' has been REJECTED.", "#6c757d"
        )
    except Exception as e:
        return HTMLResponse(
            content=create_html_response(
                "An internal server error occurred.", "#dc3545"
            ),
            status_code=500,
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
