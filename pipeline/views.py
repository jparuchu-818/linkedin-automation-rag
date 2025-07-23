from django.http import HttpResponse, Http404
from .models import Post, Topic

def create_html_response(message: str, color: str) -> str:
    """Creates a styled HTML page for the browser response."""
    icon = '✅' if color == '#28a745' else '🗑️'
    return f"""
    <html><head><title>Post Status</title><style>body{{display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif;background-color:#f0f2f5;}}.container{{text-align:center;padding:40px;border-radius:12px;background-color:white;box-shadow:0 4px 12px rgba(0,0,0,0.1);}}.status-icon{{font-size:48px;}}.message{{font-size:24px;color:#333;margin-top:20px;}}</style></head>
    <body><div class="container"><div class="status-icon" style="color:{color};">{icon}</div><div class="message">{message}</div></div></body></html>
    """

def approve_post(request, post_id: int):
    """Finds a post by its ID and updates its status to 'approved'."""
    try:
        post = Post.objects.get(pk=post_id)
        post.status = 'approved'
        post.save()
        
        # Also update the parent topic
        post.topic.status = 'processed'
        post.topic.save()
        
        html = create_html_response(f"Post for topic '{post.topic.name}' has been APPROVED.", "#28a745")
        return HttpResponse(html)
    except Post.DoesNotExist:
        raise Http404("Post not found.")

def reject_post(request, post_id: int):
    """Finds a post by its ID and updates its status to 'rejected'."""
    try:
        post = Post.objects.get(pk=post_id)
        post.status = 'rejected'
        post.save()

        # Also update the parent topic
        post.topic.status = 'processed'
        post.topic.save()

        html = create_html_response(f"Post for topic '{post.topic.name}' has been REJECTED.", "#6c757d")
        return HttpResponse(html)
    except Post.DoesNotExist:
        raise Http404("Post not found.")