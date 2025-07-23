from django.db import models

class Topic(models.Model):
    """Represents a single topic to be processed."""
    name = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default='pending') # pending, processed
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    """Represents a single piece of generated content ready for approval."""
    STATUS_CHOICES = [
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('published', 'Published'),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    generated_post = models.TextField()
    generated_image_path = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending_approval')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Post for topic: {self.topic.name} ({self.status})"
    
#jishnudosystems@mail.com