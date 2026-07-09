from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from accounts.decorators import LibrarianRequiredMixin
from .models import Book, Category
from .forms import BookForm

class BookListView(LoginRequiredMixin, ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        # Database optimization: select_related to avoid N+1 queries on category
        queryset = Book.objects.select_related('category').all().order_by('-added_date')
        
        # Search filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(ISBN__icontains=query)
            )
            
        # Category filter
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Availability filter
        availability = self.request.GET.get('availability')
        if availability == 'available':
            queryset = queryset.filter(available_copies__gt=0)
        elif availability == 'unavailable':
            queryset = queryset.filter(available_copies=0)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass categories for the filtering dropdown
        context['categories'] = Category.objects.all()
        # Keep query parameters in pagination links
        params = self.request.GET.copy()
        if 'page' in params:
            params.pop('page')
        context['query_params'] = params.urlencode()
        return context

class BookDetailView(LoginRequiredMixin, DetailView):
    model = Book
    template_name = 'catalog/book_detail.html'
    context_object_name = 'book'

    def get_queryset(self):
        return Book.objects.select_related('category')

class BookCreateView(LoginRequiredMixin, LibrarianRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'catalog/book_form.html'
    success_url = reverse_lazy('catalog:book_list')

    def form_valid(self, form):
        messages.success(self.request, f"Book '{form.instance.title}' created successfully!")
        return super().form_valid(form)

class BookUpdateView(LoginRequiredMixin, LibrarianRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'catalog/book_form.html'
    success_url = reverse_lazy('catalog:book_list')

    def get_queryset(self):
        return Book.objects.all()

    def form_valid(self, form):
        messages.success(self.request, f"Book '{form.instance.title}' updated successfully!")
        return super().form_valid(form)

class BookDeleteView(LoginRequiredMixin, LibrarianRequiredMixin, DeleteView):
    model = Book
    template_name = 'catalog/book_confirm_delete.html'
    success_url = reverse_lazy('catalog:book_list')

    def get_queryset(self):
        return Book.objects.all()

    def delete(self, request, *args, **kwargs):
        book = self.get_object()
        messages.success(self.request, f"Book '{book.title}' deleted successfully!")
        return super().delete(request, *args, **kwargs)
