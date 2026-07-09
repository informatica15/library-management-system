from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
import datetime

from accounts.decorators import LibrarianRequiredMixin, MemberRequiredMixin, librarian_required
from catalog.models import Book, Category
from .models import IssueRecord
from .forms import IssueBookForm

def update_overdue_loans():
    """Helper function to update all issued loans past due date to OVERDUE status."""
    today = timezone.now().date()
    # Find all issued records that are past due date and change status
    IssueRecord.objects.filter(status='ISSUED', due_date__lt=today).update(status='OVERDUE')

class LibrarianDashboardView(LoginRequiredMixin, LibrarianRequiredMixin, TemplateView):
    template_name = 'circulation/librarian_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_overdue_loans()

        # Database queries optimized and annotated
        context['total_books'] = Book.objects.count()
        context['total_issued'] = IssueRecord.objects.filter(status__in=['ISSUED', 'OVERDUE']).count()
        context['total_overdue'] = IssueRecord.objects.filter(status='OVERDUE').count()
        
        # Most borrowed books
        context['most_borrowed'] = Book.objects.annotate(
            borrow_count=Count('loans')
        ).filter(borrow_count__gt=0).order_by('-borrow_count')[:5]

        # Recent activities (select_related used to prevent N+1 queries)
        context['recent_loans'] = IssueRecord.objects.select_related('book', 'user').order_by('-issue_date')[:5]

        # Overdue reports
        context['overdue_records'] = IssueRecord.objects.select_related('book', 'user').filter(status='OVERDUE').order_by('due_date')

        return context

class MemberDashboardView(LoginRequiredMixin, MemberRequiredMixin, TemplateView):
    template_name = 'circulation/member_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_overdue_loans()

        user = self.request.user
        
        # Current active loans (select_related optimized)
        context['active_loans'] = IssueRecord.objects.select_related('book').filter(
            user=user, 
            status__in=['ISSUED', 'OVERDUE']
        ).order_by('due_date')

        # History of loans (select_related optimized)
        context['loan_history'] = IssueRecord.objects.select_related('book').filter(
            user=user, 
            status='RETURNED'
        ).order_by('-return_date')

        return context

class IssueBookView(LoginRequiredMixin, LibrarianRequiredMixin, CreateView):
    model = IssueRecord
    form_class = IssueBookForm
    template_name = 'circulation/issue_form.html'
    success_url = reverse_lazy('circulation:librarian_dashboard')

    def get_initial(self):
        initial = super().get_initial()
        # If book_id is in GET params, preselect book
        book_id = self.request.GET.get('book')
        if book_id:
            initial['book'] = get_object_or_404(Book, pk=book_id)
        # Pre-set default due date
        initial['due_date'] = timezone.now().date() + datetime.timedelta(days=14)
        return initial

    def form_valid(self, form):
        # Perform book decrement and loan creation atomically
        with transaction.atomic():
            loan = form.save(commit=False)
            book = loan.book
            
            # Re-verify availability to prevent race conditions
            # Lock the book row for update
            book = Book.objects.select_for_update().get(pk=book.pk)
            if book.available_copies <= 0:
                messages.error(self.request, f"Sorry, '{book.title}' is no longer available.")
                return redirect('catalog:book_list')

            book.available_copies -= 1
            book.save()
            loan.save()
            
            messages.success(self.request, f"Book '{book.title}' successfully issued to {loan.user.username}!")
            return super().form_valid(form)

@login_required
@transaction.atomic
def borrow_book_direct(request, book_id):
    """
    Action for members to borrow/checkout a book directly from the catalog.
    Enforces double borrowing prevention and copy limits.
    """
    book = get_object_or_404(Book.objects.select_for_update(), pk=book_id)
    user = request.user

    # Only members can checkout
    if hasattr(user, 'profile') and user.profile.role != 'MEMBER':
        messages.error(request, "Only library members can check out books.")
        return redirect('catalog:book_detail', pk=book_id)

    # 1. Prevent double borrowing
    existing_loan = IssueRecord.objects.filter(
        user=user,
        book=book,
        status__in=['ISSUED', 'OVERDUE']
    ).exists()
    if existing_loan:
        messages.error(request, f"You already have an active loan for '{book.title}'.")
        return redirect('catalog:book_detail', pk=book_id)

    # 2. Block issuing if copies are depleted
    if book.available_copies <= 0:
        messages.error(request, f"Sorry, '{book.title}' is currently out of stock.")
        return redirect('catalog:book_detail', pk=book_id)

    # 3. Create IssueRecord and decrement copies
    book.available_copies -= 1
    book.save()
    
    IssueRecord.objects.create(
        book=book,
        user=user,
        issue_date=timezone.now().date(),
        status='ISSUED'
    )

    messages.success(request, f"You have successfully borrowed '{book.title}'! It is due in 14 days.")
    return redirect('circulation:member_dashboard')

@login_required
@transaction.atomic
def return_book_direct(request, record_id):
    """
    Action for returning a book. Can be triggered by the borrower or a librarian.
    """
    loan = get_object_or_404(IssueRecord.objects.select_for_update(), pk=record_id)
    
    # Check permissions (either borrower themselves or librarian)
    is_librarian = hasattr(request.user, 'profile') and request.user.profile.role == 'LIBRARIAN'
    if loan.user != request.user and not is_librarian:
        messages.error(request, "You do not have permission to return this book.")
        return redirect('catalog:book_list')

    if loan.status == 'RETURNED':
        messages.warning(request, "This book has already been returned.")
        return redirect('catalog:book_list')

    # Update book copy counts
    book = Book.objects.select_for_update().get(pk=loan.book.pk)
    book.available_copies += 1
    if book.available_copies > book.total_copies:
        book.available_copies = book.total_copies
    book.save()

    # Update loan record
    loan.return_date = timezone.now().date()
    loan.status = 'RETURNED'
    loan.save()

    messages.success(request, f"Book '{book.title}' has been successfully returned!")
    
    # Redirect based on who returned it
    if is_librarian:
        return redirect('circulation:librarian_dashboard')
    return redirect('circulation:member_dashboard')

class OverdueReportsListView(LoginRequiredMixin, LibrarianRequiredMixin, ListView):
    model = IssueRecord
    template_name = 'circulation/overdue_report.html'
    context_object_name = 'overdue_loans'

    def get_queryset(self):
        update_overdue_loans()
        return IssueRecord.objects.select_related('book', 'user').filter(status='OVERDUE').order_by('due_date')
