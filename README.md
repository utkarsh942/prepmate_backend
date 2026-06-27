# PrepMate - AI Study Platform (Backend)

The backend for PrepMate, an AI-powered study platform that automatically converts your PDF notes into interactive quizzes, flashcards, and summaries.

##  Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database:** MongoDB (Atlas)
- **AI Integration:** Google Gemini (2.5 Flash)
- **Authentication:** Google OAuth 2.0 & JWT (JSON Web Tokens)
- **PDF Processing:** PyMuPDF (`fitz`)

##  Key Features

- **Google Authentication:** Secure login using Google Identity Services.
- **PDF Extraction:** Efficiently extracts text from uploaded PDF documents.
- **AI Generation:** Uses Google's Gemini AI to generate:
  - Smart study flashcards (Question & Answer format).
  - NTA/JEE style multiple-choice quizzes with explanations.
  - Comprehensive document summaries.
- **User Analytics:** Tracks quiz attempts, scores, and weekly activity.
- **Caching Mechanism:** Saves generated AI content to MongoDB to reduce API calls and improve load times.

##  Local Development Setup

### Prerequisites
- Python 3.9+
- MongoDB Atlas account (or local MongoDB)
- Google Cloud Console account (for OAuth Client ID)
- Google Gemini API Key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/prepmate-backend.git
   cd prepmate-backend
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add the following keys:
   ```env
   MONGO_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/
   GEMINI_API_KEY=your_gemini_api_key_here
   GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
   JWT_SECRET_KEY=your_super_secret_jwt_key
   ```

5. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The API will be available at `http://localhost:8000`. You can view the interactive API documentation at `http://localhost:8000/docs`.

##  Deployment

This backend is configured for easy deployment on platforms like **Render**.
- Uses `uvicorn app.main:app --host 0.0.0.0 --port $PORT` as the start command.
- Includes `pymongo[srv]` and `python-jose` for production stability.
- CORS is currently configured to allow all origins (`*`) for easy integration with the frontend.
