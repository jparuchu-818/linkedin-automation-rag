
from django.contrib import admin
from .models import Topic, Post

# This "registers" your models with the Django admin site.
admin.site.register(Topic)
admin.site.register(Post)