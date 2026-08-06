# AI Classroom Assistant — Backend Architecture

This document describes the backend systems architecture, layout design, and pipeline flows for the AI Classroom Assistant.

## Architectural Layers

The backend follows a **three-tier web architecture** adhering to SOLID principles and Clean Architecture paradigms:

```
[ HTTP Requests ]
       │
       ▼
┌──────────────┐
│  API Routes  │  FastAPI Path Operations & Path Parameter Validation
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Services     │  Business logic encapsulation (auth, AI generators, summarizers)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Repositories │  Database operations (Queries, inserts, updates)
└──────┬───────┘
       │
       ▼
[ PostgreSQL DB ]
```

1. **API Routing Layer (`app/api/`)**: Declares FastAPIRouters, path validation parameters, Pydantic Input/Output validations, and auth dependencies.
2. **Service Layer (`app/services/` & `app/ai/services/`)**: Orchestrates business workflows, file handling, external API communication (Gemini/OpenAI), and RAG execution loops.
3. **Repository Layer (`app/repositories/`)**: Encapsulates all database persistence operations, abstracting SQLAlchemy raw queries away from business operations.

---

## Authentication and Role-Based Access Control (RBAC)

The authentication system employs JSON Web Tokens (JWT) using the `HS256` signature algorithm.

### Token Flow
1. **User Login**: User submits email/password. System returns an `access_token` (expires in 30-60 mins) and a `refresh_token` (expires in 7 days).
2. **Accessing Routes**: The frontend places the `access_token` in the HTTP header: `Authorization: Bearer <access_token>`.
3. **Role Checks**: Custom dependency injection `RoleChecker([UserRole.TEACHER, UserRole.ADMIN])` decodes the token, inspects the payload `role` claim, and rejects/accepts execution accordingly.
4. **Token Refresh**: When the access token expires, the client calls the `/api/v1/auth/refresh` route with their `refresh_token` to receive a fresh token pair.

---

## AI Module & RAG Pipeline Architecture

```
┌─────────────────┐
│ Document Upload │ (PDF, DOCX, PPTX)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Text Extraction │ via PyMuPDF (PDF), python-docx (DOCX), python-pptx (PPTX)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Embeddings Gen  │ via Sentence Transformers (all-MiniLM-L6-v2)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Database │ Local FAISS indices stored in `/vector_indices`
└─────────────────┘
```

1. **Document Ingestion**: File uploaded by student/teacher is stored locally (or on S3 in production).
2. **Text Processing**: Text is parsed and chunked.
3. **Embeddings & Vector Indexing**: The `VectorIndexManager` computes float vector dimensions via standard `SentenceTransformer` encoders, feeding them into a local `FAISS` L2 proximity search database.
4. **Retrieval & LLM generation**: Users query the chatbot, matching similarity blocks via FAISS, then submitting context vectors along with queries to the LangChain Google Gemini model wrapper.
