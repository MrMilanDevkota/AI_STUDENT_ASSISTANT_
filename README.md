# 🎓 AI Study Assistant

A production-ready Django web application that helps students study smarter using AI.
Upload PDF, DOCX, or TXT files and get AI-powered summaries, quizzes, flashcards, and a chat tutor.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📤 **Document Upload** | PDF, DOCX, TXT support (up to 10MB) |
| 📝 **Summaries** | Short summary, detailed summary, key concepts |
| ❓ **Quiz Generator** | 10 MCQs + 5 short answer questions with answers |
| 🗂 **Flashcards** | Interactive flip cards for active recall |
| 💬 **Chat with Notes** | RAG-powered Q&A using your uploaded documents |
| 🔐 **Authentication** | Register, login, logout |

---

## 🛠 Tech Stack

- **Backend:** Django 5, Python 3.11+
- **AI:** LangChain + Google Gemini 1.5 Flash
- **Vector DB:** FAISS (local, no server needed)
- **Embeddings:** Google Generative AI Embeddings (or HuggingFace fallback)
- **Document Processing:** pypdf, python-docx
- **Frontend:** Bootstrap 5, vanilla JS

---

## 📁 Project Structure

```
ai_study_assistant/
├── manage.py
├── requirements.txt
├── .env.example                 ← Copy to .env
│
├── config/                      ← Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── accounts/                    ← User auth (register/login/logout)
│   ├── models.py                ← UserProfile
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── study_materials/             ← Core app
│   ├── models.py                ← StudyMaterial, AIGeneratedContent, ChatMessage
│   ├── views.py                 ← All feature views
│   ├── forms.py                 ← Upload form with validation
│   └── urls.py
│
├── ai_services/                 ← AI logic (separated from views)
│   ├── document_loader.py       ← PDF/DOCX/TXT text extraction
│   ├── text_splitter.py         ← Chunk documents for embedding
│   ├── embeddings.py            ← Google or HuggingFace embeddings
│   ├── vector_store.py          ← FAISS create/load/search
│   ├── llm.py                   ← Google Gemini LLM setup
│   ├── document_processor.py    ← Orchestrates the ingestion pipeline
│   ├── summarizer.py            ← Summary generation
│   ├── quiz_generator.py        ← MCQ + short question generation
│   ├── flashcard_generator.py   ← Flashcard generation
│   └── chat_engine.py           ← RAG-based Q&A
│
├── templates/                   ← Global templates
│   └── base.html
│
├── static/                      ← Static files (CSS/JS)
└── media/                       ← Uploaded files + FAISS indexes
    ├── study_materials/
    └── vector_stores/
```

---

## 🚀 Setup Instructions

### Step 1: Get a Free Google Gemini API Key

1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with Google
3. Click **"Create API Key"**
4. Copy the key

### Step 2: Clone & Create Virtual Environment

```bash
# Navigate to project directory
cd ai_study_assistant

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Note:** First-time install may take 2–5 minutes due to AI packages.
> If you get errors with `faiss-cpu`, try: `pip install faiss-cpu --no-cache-dir`

### Step 4: Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your values:
GOOGLE_API_KEY=your-actual-gemini-api-key-here
SECRET_KEY=any-long-random-string-here
DEBUG=True
```

### Step 5: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### Step 7: Start the Development Server

```bash
python manage.py runserver
```

Open your browser: **http://localhost:8000**

---

## 📖 Example Workflow

1. **Register** at `/accounts/register/`
2. **Login** and go to the **Dashboard**
3. Click **"Upload Material"** → upload a PDF/DOCX/TXT
4. Wait for processing (10–30 seconds for most files)
5. Once status shows **"Ready"**, use the AI features:
   - 📝 **Summary** → Get short, detailed summary + key concepts
   - ❓ **Quiz** → Take an MCQ quiz, check answers with explanations
   - 🗂 **Flashcards** → Review with flippable cards (keyboard: arrow keys + space)
   - 💬 **Chat** → Ask questions in natural language

---

## ⚙️ AI Pipeline Explained

```
Upload File
    ↓
Extract Text (pypdf / python-docx / plain text)
    ↓
Split into Chunks (1000 chars, 200 overlap)
    ↓
Generate Embeddings (Google Embedding API)
    ↓
Store in FAISS Vector Index (saved to disk)
    ↓
[Ready for AI Features]
    ↓
User Question → Embed Question → Find Top-K Similar Chunks
    ↓
Context + Question → Gemini LLM → Answer
```

---

## 🔧 Troubleshooting

**"GOOGLE_API_KEY not set"**
→ Make sure your `.env` file exists and has the correct key.

**"faiss-cpu install error"**
→ Try: `pip install faiss-cpu --no-cache-dir`

**"No text could be extracted from PDF"**
→ The PDF may be scanned/image-based. Use a text-based PDF or OCR it first.

**AI features give errors**
→ Check your API key quota at https://aistudio.google.com
→ Gemini free tier has rate limits; wait a moment and retry.

**HuggingFace model download on first use**
→ Normal behavior if GOOGLE_API_KEY not set. Model (~90MB) downloads once.

---

## 🔒 Security Notes for Production

- Set `DEBUG=False`
- Use a strong random `SECRET_KEY`
- Configure PostgreSQL instead of SQLite
- Use proper file storage (AWS S3, etc.)
- Set `ALLOWED_HOSTS` to your domain

---

## 📄 License

MIT License — Free for personal and educational use.
