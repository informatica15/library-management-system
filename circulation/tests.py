from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import datetime

from catalog.models import Book, Category
from circulation.models import IssueRecord, get_default_due_date
from accounts.models import UserProfile

class LibraryManagementSystemTests(TestCase):
    def setUp(self):
        # 1. Create a Category
        self.category = Category.objects.create(
            name="Test Science",
            description="Science test category"
        )
        
        # 2. Create Books
        self.book_available = Book.objects.create(
            title="Introduction to Physics",
            author="Dr. Albert",
            ISBN="123-4567890123",
            category=self.category,
            total_copies=5,
            available_copies=5
        )
        
        self.book_empty = Book.objects.create(
            title="Quantum Mechanics for Beginners",
            author="Dr. Bohr",
            ISBN="987-6543210987",
            category=self.category,
            total_copies=2,
            available_copies=0
        )

        # 3. Create Users (signals will auto-create profiles as MEMBER by default)
        self.member_user = User.objects.create_user(
            username="member1",
            password="password123",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com"
        )
        
        self.librarian_user = User.objects.create_user(
            username="librarian1",
            password="password123",
            first_name="John",
            last_name="Smith",
            email="john@example.com"
        )
        # Update librarian's role to LIBRARIAN
        self.librarian_user.profile.role = 'LIBRARIAN'
        self.librarian_user.profile.save()

        # 4. Set up Clients for testing views
        self.member_client = Client()
        self.member_client.login(username="member1", password="password123")

        self.librarian_client = Client()
        self.librarian_client.login(username="librarian1", password="password123")

    def test_profile_creation_and_roles(self):
        """Verify that user profiles and roles are created correctly."""
        self.assertEqual(self.member_user.profile.role, 'MEMBER')
        self.assertEqual(self.librarian_user.profile.role, 'LIBRARIAN')

    def test_direct_borrowing_logic(self):
        """Test borrowing a book directly updates copy count and creates record."""
        # Member borrows available book
        response = self.member_client.post(
            reverse('circulation:borrow_book_direct', args=[self.book_available.id])
        )
        
        # Should redirect to member dashboard
        self.assertRedirects(response, reverse('circulation:member_dashboard'))
        
        # Verify book copies decremented
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, 4)
        
        # Verify issue record is created
        loan = IssueRecord.objects.get(user=self.member_user, book=self.book_available)
        self.assertEqual(loan.status, 'ISSUED')
        self.assertIsNone(loan.return_date)

    def test_block_borrowing_if_no_copies(self):
        """Test that borrowing is blocked when available copies is 0."""
        response = self.member_client.post(
            reverse('circulation:borrow_book_direct', args=[self.book_empty.id])
        )
        
        # Should redirect back to detail view
        self.assertRedirects(response, reverse('catalog:book_detail', args=[self.book_empty.id]))
        
        # Verify no copies changed
        self.book_empty.refresh_from_db()
        self.assertEqual(self.book_empty.available_copies, 0)
        
        # Verify no loan record created
        loans_exist = IssueRecord.objects.filter(user=self.member_user, book=self.book_empty).exists()
        self.assertFalse(loans_exist)

    def test_double_borrowing_prevention(self):
        """Test that members cannot borrow the same book simultaneously."""
        # First borrow
        self.member_client.post(reverse('circulation:borrow_book_direct', args=[self.book_available.id]))
        
        # Second borrow of same book
        response = self.member_client.post(reverse('circulation:borrow_book_direct', args=[self.book_available.id]))
        
        # Should redirect with warning back to detail
        self.assertRedirects(response, reverse('catalog:book_detail', args=[self.book_available.id]))
        
        # Copies should only decrement once (from 5 to 4)
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, 4)
        
        # Only 1 record should exist
        loans_count = IssueRecord.objects.filter(user=self.member_user, book=self.book_available).count()
        self.assertEqual(loans_count, 1)

    def test_returning_book_logic(self):
        """Test returning a book updates copy counts and record status."""
        # Create an active loan first
        loan = IssueRecord.objects.create(
            book=self.book_available,
            user=self.member_user,
            status='ISSUED'
        )
        self.book_available.available_copies -= 1
        self.book_available.save()

        # Perform return
        response = self.member_client.post(reverse('circulation:return_book_direct', args=[loan.id]))
        self.assertRedirects(response, reverse('circulation:member_dashboard'))

        # Verify book copies incremented
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, 5)

        # Verify record updated
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'RETURNED')
        self.assertEqual(loan.return_date, timezone.now().date())

    def test_overdue_flagging(self):
        """Test that books are auto-flagged as overdue when past their due date."""
        past_due = timezone.now().date() - datetime.timedelta(days=1)
        loan = IssueRecord.objects.create(
            book=self.book_available,
            user=self.member_user,
            due_date=past_due,
            status='ISSUED'
        )
        
        # Verify check updates status
        is_overdue = loan.check_and_update_overdue()
        self.assertTrue(is_overdue)
        self.assertEqual(loan.status, 'OVERDUE')

    def test_rbac_view_restrictions(self):
        """Verify that dashboard views correctly restrict roles."""
        # 1. Member tries to access librarian dashboard -> should redirect to catalog:book_list with error
        response = self.member_client.get(reverse('circulation:librarian_dashboard'))
        self.assertRedirects(response, reverse('catalog:book_list'))

        # 2. Librarian tries to access member dashboard -> should redirect to catalog:book_list with error
        response = self.librarian_client.get(reverse('circulation:member_dashboard'))
        self.assertRedirects(response, reverse('catalog:book_list'))

        # 3. Librarian accesses librarian dashboard -> 200 OK
        response = self.librarian_client.get(reverse('circulation:librarian_dashboard'))
        self.assertEqual(response.status_code, 200)

        # 4. Member accesses member dashboard -> 200 OK
        response = self.member_client.get(reverse('circulation:member_dashboard'))
        self.assertEqual(response.status_code, 200)
