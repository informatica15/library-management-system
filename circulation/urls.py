from django.urls import path
from . import views

app_name = 'circulation'

urlpatterns = [
    path('dashboard/librarian/', views.LibrarianDashboardView.as_view(), name='librarian_dashboard'),
    path('dashboard/member/', views.MemberDashboardView.as_view(), name='member_dashboard'),
    path('issue/', views.IssueBookView.as_view(), name='issue_book'),
    path('borrow/<int:book_id>/', views.borrow_book_direct, name='borrow_book_direct'),
    path('return/<int:record_id>/', views.return_book_direct, name='return_book_direct'),
    path('overdue/', views.OverdueReportsListView.as_view(), name='overdue_report'),
]
