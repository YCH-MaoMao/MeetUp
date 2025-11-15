from django.db import models
from django.contrib.auth.models import AbstractUser

# User model
class User(AbstractUser):
    email = models.EmailField(blank=True, null=True, unique=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20)
    bio = models.TextField(blank=True, null=True) 
    
    def __str__(self):
        return self.username
    

# Category model
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# Activity model
class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    date_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    max_participants = models.IntegerField()
    status = models.CharField(max_length=50, default='active')
    participants = models.ManyToManyField(User, related_name='activities_participated', blank=True)
    
    def __str__(self):
        return self.title

# Address model
class Address(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.street}, {self.city}"

# Rating model
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    score = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    review_text = models.TextField()
    
    def __str__(self):
        return f"Rating {self.score} by {self.user.username}"

# Comment model
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.username}"

# UserPreference model
class UserPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preferred_categories = models.CharField(max_length=255)
    privacy_settings = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Preferences of {self.user.username}"

# Conversation model
class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Message model
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Message from {self.sender.username}"

# IssueReport model
class IssueReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    issue_type = models.IntegerField()
    detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Issue {self.issue_type} by {self.user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

# JoinRequest model
class JoinRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='join_requests')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'activity')  # Prevent duplicate requests
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s request to join {self.activity.title}"