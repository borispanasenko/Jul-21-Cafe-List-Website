# Jul-21-Cafe-List-Website

## Overview
Cafe List Website is a web application for browsing and managing a list of cafes. It features a user-facing frontend inspired by Tripadvisor's UI for searching cafes by city and categories, and an admin panel for CRUD operations (create, read, update, delete cafes). The backend is built with FastAPI (Python), using JWT authentication and SQLite database. The frontend is simple HTML/JS/CSS with dynamic filtering and modals.

Key features:
- User page: Search cafes by city, filter by primary ("Best For") and additional categories.
- Admin page: Login, add/edit/delete cafes, with category selection.
- Responsive design with modern styling (white/green theme, cards, animations).

## Setup and Launch

### Prerequisites
- Python 3.10+ installed.
- Git for cloning the repository.

### Steps
1. **Clone the Repository**:
   ```
   git clone https://github.com/your_username/cafe-finder.git
   cd cafe-finder
   ```

2. **Install Dependencies**:
   Install Python packages from `requirements.txt` (includes FastAPI, SQLAlchemy, PyJWT, python-dotenv, etc.):
   ```
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory with the following content (replace `SECRET_KEY` with a secure random string, e.g., generated via `python -c 'import secrets; print(secrets.token_hex(32))'`):
   ```
   # .env
   SECRET_KEY=your_secure_random_key_here
   ENV=development
   DEBUG=True
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. **Run the Backend**:
   Start the FastAPI server:
   ```
   python run.py
   ```
   - The API will be available at `http://127.0.0.1:8000`.
   - Access Swagger UI for API docs at `http://127.0.0.1:8000/docs`.

5. **Run the Frontend**:
   - Open `public/index.html` in a browser for the user page.
   - Open `public/admin.html` in a browser for the admin panel.
   - Note: The frontend connects to the backend API at `http://127.0.0.1:8000`. Ensure the server is running.

6. **Test the Application**:
   - Admin: Login via admin page (use credentials from your setup; default may require seeding DB via `scripts/seed_db.py`).
   - User: Search cafes by city and apply filters.
   - If needed, seed the database: `python app/scripts/seed_db.py`.

## Future Improvements
- Externalize CSS/JS for better maintainability.
- Add more features like image uploads or advanced search.
- Deploy to production (e.g., Heroku/AWS for backend, GitHub Pages for frontend).

For issues or contributions, open a pull request or issue on GitHub.