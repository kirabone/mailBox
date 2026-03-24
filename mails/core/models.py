from django.db import models
from django.contrib.auth.models import User

class Mail(models.Model):
    sender = models.ForeignKey(User, related_name='sent_mails', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_mails', on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_receiver = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.recipient}"