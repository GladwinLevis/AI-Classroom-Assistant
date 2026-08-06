# AI Classroom Assistant Platform 🎓⚡

> Production-grade, AI-powered enterprise educational SaaS backend and web application built with FastAPI, React, PostgreSQL, Redis, Celery, LangChain, SentenceTransformers, and Google Gemini API.

---

## 🌟 Modules & Core Capabilities

1. **Authentication & Access Control (RBAC)**: JWT access/refresh token rotation, Redis token blacklist, bcrypt password hashing, and Student/Teacher/Admin role permissions.
2. **Attendance Management System**: QR-code scanning attendance sessions, geofenced location validation, automated low-attendance alerts, and teacher overrides.
3. **AI Notes & Summarization Engine**: Document parsing (PDF, DOCX, PPTX, TXT), key point extraction, chapter-wise summaries, and flashcard generation via Google Gemini.
4. **AI Doubt Chatbot (RAG)**: Retrieval-Augmented Generation powered by FAISS vector embeddings, SentenceTransformers, streaming responses, and conversation memory.
5. **AI Assignment Checker**: Modular plagiarism detection engine (`SimilarityService`), rubric criteria grading, grammar/structure feedback, and teacher grade approval workflows.
6. **AI Quiz Generator & Assessment Engine**: Automated question generation across Bloom's Taxonomy levels (*Remember, Understand, Apply, Analyze, Evaluate, Create*), instant MCQ auto-grading, AI subjective evaluation, adaptive study recommendations, and course leaderboards.
7. **Enterprise Dashboard & Analytics**: Recharts-compatible chart series for Student, Teacher, and Admin views with multi-dimensional performance tracking.
8. **Reporting Engine**: Asynchronous generation and downloading of PDF, Excel, and CSV academic reports.
9. **Global Search & Activity Timeline**: Multi-entity search across courses, quizzes, assignments, documents, and user action activity logging.

---

## 🛠️ Architecture & Tech Stack

- **Backend**: FastAPI, Async SQLAlchemy 2.0, Pydantic V2, Alembic
- **AI & RAG**: Google Gemini API (`gemini-2.5-flash`), LangChain, FAISS, SentenceTransformers
- **Async Workers & Caching**: Celery, Redis, PostgreSQL 16
- **Frontend**: React, TypeScript, Vite, TailwindCSS, Lucide Icons, Recharts
- **Containerization & CI/CD**: Docker, Docker Compose, Nginx, GitHub Actions

---

## 🚀 Quick Start (Local & Docker)

### Option A: Docker Compose (Recommended)
```bash
# Clone repository
git clone https://github.com/your-org/ai-classroom-assistant.git
cd ai-classroom-assistant

# Start all multi-container services
docker-compose up --build -d
```
The application will be accessible at:
- **Frontend**: `http://localhost`
- **Backend API Docs**: `http://localhost/api/v1/docs`

### Option B: Local Development Setup
Refer to [docs/INSTALLATION.md](file:///c:/Users/Levis/OneDrive/Desktop/ai-classroom-assistant/docs/INSTALLATION.md) for full step-by-step instructions.

---

## 📚 Documentation

- [Installation Guide](file:///c:/Users/Levis/OneDrive/Desktop/ai-classroom-assistant/docs/INSTALLATION.md)
- [System Architecture & Data Flow](file:///c:/Users/Levis/OneDrive/Desktop/ai-classroom-assistant/docs/ARCHITECTURE.md)
- [API Reference & Swagger Docs](file:///c:/Users/Levis/OneDrive/Desktop/ai-classroom-assistant/docs/API_GUIDE.md)
- [Production Deployment Guide](file:///c:/Users/Levis/OneDrive/Desktop/ai-classroom-assistant/docs/DEPLOYMENT.md)
