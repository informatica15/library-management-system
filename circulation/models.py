import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from catalog.models import Book

def get_default_due_date():
    return timezone.now().date() + datetime.timedelta(days=14)

class IssueRecord(models.Model):
    STATUS_CHOICES = (
        ('ISSUED', 'Issued'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(default=get_default_due_date, db_index=True)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ISSUED', db_index=True)

    def save(self, *args, **kwargs):
        # Auto-update status to OVERDUE if the book is issued but today is past the due date
        if self.status == 'ISSUED' and self.due_date < timezone.now().date():
            self.status = 'OVERDUE'
        super().save(*args, **kwargs)

    def check_and_update_overdue(self):
        if self.status == 'ISSUED' and self.due_date < timezone.now().date():
            self.status = 'OVERDUE'
            self.save(update_fields=['status'])
        return self.status == 'OVERDUE'

    def __str__(self):
        return f"{self.user.username} -> {self.book.title} ({self.status})"
