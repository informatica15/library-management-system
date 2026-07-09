from django import forms
from .models import Book, Category

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'ISBN', 'category', 'total_copies', 'available_copies', 'cover_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
            'author': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
            'ISBN': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
            'total_copies': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
            'available_copies': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300'}),
            'cover_image': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 bg-white text-slate-800 border-slate-300', 'placeholder': 'https://images.unsplash.com/... (optional)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_copies = cleaned_data.get('total_copies')
        available_copies = cleaned_data.get('available_copies')
        
        if total_copies is not None and available_copies is not None:
            if available_copies > total_copies:
                raise forms.ValidationError("Available copies cannot exceed total copies.")
        return cleaned_data
