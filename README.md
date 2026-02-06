# Financial AI Backend

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    -   Copy `.env.example` to `.env`.
    -   Update `DATABASE_URL` with your PostgreSQL credentials.
    -   Add your `GEMINI_API_KEY`.

3.  **Run Database Migrations (Auto-create tables):**
    The app is configured to create tables automatically on the first run.

4.  **Start Server:**
    ```bash
    python app.py
    ```

## API Endpoints

-   `POST /api/auth/register`: Create a new user account.
-   `POST /api/auth/login`: Login and receive JWT token.
-   `POST /api/analyze`: Upload files for AI analysis (Requires `Authorization: Bearer <token>`).
