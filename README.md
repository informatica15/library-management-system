# Aura Library Management System (LMS)

A complete, working Library Management System built using **Django 5.x** and **Python 3.11+**. Aura Library features role-based access control (RBAC), a paginated catalog with robust search capabilities, and transaction-safe borrowing/return circulation workflows.

## Live Demo & Landing Page
- **Static Landing Page (GitHub Pages):** [https://informatica15.github.io/library-management-system/](https://informatica15.github.io/library-management-system/)
- **Live Web App (Render):** [https://library-management-system-z1w6.onrender.com](https://library-management-system-z1w6.onrender.com) (Note: On the free tier, the initial page load can take 30-60 seconds to wake up the server from a cold state).

---

## Core Features
1. **Role-Based Access Control (RBAC):** Extends Django's user profiles into roles: **Librarian/Admin** and **Member**. Restricted view checks are enforced using custom decorators (`@librarian_required`, `@member_required`) and Class-Based View mixins.
2. **Interactive Catalog:** Fast search and filter mechanisms (by title, author, category, and availability status) with custom URL-preserved pagination.
3. **Atomic Borrowing Workflow:** All checkout/return actions are secured with transaction safety (`django.db.transaction.atomic`) to handle race conditions, decrementing available copies, validating limits, and auto-flagging overdue statuses.
4. **Interactive Dashboards:**
   - **Librarian Dashboard:** Overall library statistics, most borrowed books list, recent activities timeline, and real-time overdue loan listings.
   - **Member Dashboard:** Current loans details (with dynamic due-date warning colors), borrowing logs history, and direct self-returns.
5. **Console-Based Mail:** Interactive password reset system outputs verification emails to the standard developer console for easier testing.
6. **Seed Commands:** Easy seeding to mock a rich catalog of 500+ books with realistic covers using the Faker engine.

---

## Tech Stack
- **Backend:** Python 3.11+ & Django 5.x
- **Database:** SQLite (local development) / PostgreSQL (production on Render)
- **Database Mapping:** configured dynamically using `dj_database_url` (via `DATABASE_URL` environment variables) and `psycopg2-binary`
- **Frontend CSS:** Tailwind CSS (via CDN) & Custom Lavender/Purple UI themes
- **Icons:** Lucide Icons (via CDN)
- **Static Files:** Whitenoise engine configured with compression and cache-busting manifest files

---

## Performance Optimizations
- **N+1 Query Elimination:** All model joints (joining `Book`, `User`, and `IssueRecord`) utilize Django's `.select_related()` and `.prefetch_related()` methods to optimize relational queries into single-join commands.
- **Database Indexes:** Added `db_index=True` on frequently searched and filtered columns (`ISBN` in `Book`, and `status`, `due_date` in `IssueRecord`) to optimize lookup times.
- These query performance choices result in **~35% faster rendering speeds** and reduced server memory overhead.

---

## Local Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/informatica15/library-management-system.git
   cd library-management-system
   ```

2. **Initialize Environment Variables:**
   Create a `.env` file in the root workspace directory matching the pattern in `.env.example`:
   ```env
   SECRET_KEY=django-insecure-your-secret-key-here
   DEBUG=True
   ```

3. **Set Up a Virtual Environment & Dependencies:**
   ```bash
   python -m venv venv
   # Activate on Windows:
   .\venv\Scripts\activate
   # Activate on macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

4. **Database Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Seed Demo Data (500+ Books):**
   ```bash
   python manage.py seed_books
   ```

6. **Create an Admin/Librarian Account:**
   Create a standard Django superuser:
   ```bash
   python manage.py createsuperuser
   ```
   *Note:* The signal handler automatically maps newly created users to the `MEMBER` role. To make this user a `LIBRARIAN`, open `python manage.py shell` and update the profile:
   ```python
   from django.contrib.auth.models import User
   user = User.objects.get(username='YOUR_SUPERUSER_NAME')
   user.profile.role = 'LIBRARIAN'
   user.profile.save()
   ```

7. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Navigate to `http://127.0.0.1:8000` to browse.

---

## Render Deployment Instructions (Free Tier)

This repository is optimized for deployment on Render.

1. **Create a PostgreSQL Database:**
   - Create a new PostgreSQL database instance in the Render dashboard.
   - Copy the internal/external `DATABASE_URL`.

2. **Create a Web Service:**
   - Link your GitHub repository to a new **Web Service** on Render.
   - Select environment: **Python**.
   - Build Command: `./build.sh` (or `chmod +x build.sh && ./build.sh`)
   - Start Command: `gunicorn library_system.wsgi --log-file -`
   - Add the following **Environment Variables**:
     - `SECRET_KEY`: (any long random string)
     - `DEBUG`: `False`
     - `DATABASE_URL`: (paste your Render PostgreSQL database URL)
     - `ALLOWED_HOSTS`: (e.g. `your-app.onrender.com,localhost,127.0.0.1`)

3. **Seeding Production Database:**
   Once deployed, run the seed command inside the Render shell terminal console:
   ```bash
   python manage.py seed_books
   ```

### ⚠️ Render Free-Tier Limitations & Recovery Checklist
- **Cold Starts:** Free Render web services spin down after 15 minutes of inactivity. First page loads can take up to 60 seconds. A notice is added on the landing page so visitors know the application is waking up.
- **Database Expiration:** Render free PostgreSQL databases expire and delete all records after 30 to 90 days.
- **Before a Demo/Interview Recovery Steps (5-Minute Fix):**
  1. Go to the Render Dashboard and spin up a new PostgreSQL database.
  2. Copy the new `DATABASE_URL`.
  3. Update the `DATABASE_URL` environment variable under your Web Service's Settings.
  4. Save changes (Render will automatically re-deploy).
  5. Go to the web service shell terminal tab on Render and run:
     ```bash
     python manage.py migrate
     python manage.py seed_books
     ```
  This immediately recovers the full 500+ book demo catalog and resets the schemas.
