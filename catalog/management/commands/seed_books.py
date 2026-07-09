import random
from django.core.management.base import BaseCommand
from catalog.models import Book, Category
from faker import Faker

class Command(BaseCommand):
    help = 'Seeds the database with sample categories and 500+ realistic books'

    def handle(self, *args, **options):
        self.stdout.write('Seeding categories and books...')
        fake = Faker()
        
        # 1. Define standard categories
        category_names = [
            'Fiction', 'Science & Tech', 'Biography', 'History', 
            'Philosophy', 'Self-Help', 'Business & Finance', 
            'Mystery & Thriller', 'Art & Photography', 'Poetry'
        ]
        
        categories = []
        for name in category_names:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': f'A collection of books related to {name}.'}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {name}')

        # 2. Predefined list of high-quality Unsplash book photo IDs for realistic covers
        unsplash_photo_ids = [
            'photo-1543002588-bfa74002ed7e',
            'photo-1544947950-fa07a98d237f',
            'photo-1512820790803-83ca734da794',
            'photo-1497633762265-9d179a990aa6',
            'photo-1516979187457-637abb4f9353',
            'photo-1495446815901-a7297e633e8d',
            'photo-1506880018603-83d5b814b5a6',
            'photo-1532012197267-da84d127e765',
            'photo-1476275466078-4007374efbbe',
            'photo-1456513080510-7bf3a84b82f8'
        ]

        # 3. Create 500+ books
        books_to_create = 520
        existing_isbns = set(Book.objects.values_list('ISBN', flat=True))
        created_count = 0

        # Generate unique ISBN helper
        def generate_unique_isbn():
            while True:
                isbn = fake.isbn13()
                if isbn not in existing_isbns:
                    existing_isbns.add(isbn)
                    return isbn

        # Some realistic sounding words for book titles
        adjectives = ['Ancient', 'Silent', 'Lost', 'Forgotten', 'Golden', 'Dark', 'Hidden', 'Infinite', 'Shattered', 'Whispering', 'The Last', 'The Great']
        nouns = ['Empire', 'Secret', 'Legacy', 'Chronicle', 'Shadow', 'Journey', 'Valley', 'Star', 'Dream', 'Kingdom', 'Path', 'Horizon']
        subjects = ['of Time', 'in the Rain', 'of the Wind', 'of Knowledge', 'under the Stars', 'of the Mind', 'of Tomorrow', 'of History']

        self.stdout.write(f'Generating {books_to_create} books, please wait...')
        
        books = []
        for _ in range(books_to_create):
            # Formulate title
            title_type = random.choice([1, 2, 3])
            if title_type == 1:
                title = f"{random.choice(adjectives)} {random.choice(nouns)}"
            elif title_type == 2:
                title = f"The {random.choice(nouns)} {random.choice(subjects)}"
            else:
                title = f"{random.choice(adjectives)} {random.choice(nouns)} {random.choice(subjects)}"

            author = fake.name()
            isbn = generate_unique_isbn()
            category = random.choice(categories)
            total_copies = random.randint(3, 10)
            # randomly some copies can be currently checked out in a real db, but we initialize available_copies = total_copies
            available_copies = total_copies
            
            photo_id = random.choice(unsplash_photo_ids)
            cover_image = f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&q=80&w=300&h=450"

            books.append(Book(
                title=title,
                author=author,
                ISBN=isbn,
                category=category,
                total_copies=total_copies,
                available_copies=available_copies,
                cover_image=cover_image
            ))
            
            # Bulk create in batches of 100
            if len(books) >= 100:
                Book.objects.bulk_create(books)
                created_count += len(books)
                self.stdout.write(f'Successfully created {created_count} books...')
                books = []

        if books:
            Book.objects.bulk_create(books)
            created_count += len(books)
            self.stdout.write(f'Successfully created {created_count} books...')

        self.stdout.write(self.style.SUCCESS(f'Finished seeding! Created {created_count} books.'))
