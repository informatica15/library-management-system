from django import forms
from django.contrib.auth.models import User
from catalog.models import Book
from .models import IssueRecord

class IssueBookForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_superuser=False),
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
        label="Select Member"
    )
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(available_copies__gt=0),
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
        label="Select Book"
    )

    class Meta:
        model = IssueRecord
        fields = ['user', 'book', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        book = cleaned_data.get('book')

        if user and book:
            # Check if this user already has this book checked out
            existing_loan = IssueRecord.objects.filter(
                user=user,
                book=book,
                status__in=['ISSUED', 'OVERDUE']
            ).exists()
            if existing_loan:
                raise forms.ValidationError(f"This user has already borrowed '{book.title}' and has not returned it yet.")
            
            # Check if book is available
            if book.available_copies <= 0:
                raise forms.ValidationError("This book currently has no copies available for loan.")
                
        return cleaned_data
