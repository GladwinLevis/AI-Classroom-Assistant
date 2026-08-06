# API Reference & Swagger Guide

The AI Classroom Assistant backend exposes RESTful APIs documented automatically with OpenAPI 3.0.

- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## Endpoint Summary

### Authentication (`/api/v1/auth`)
- `POST /register`: Register user account
- `POST /login`: Generate JWT access and refresh tokens
- `POST /refresh`: Rotate refresh token
- `POST /logout`: Blacklist token in Redis

### Health Probes (`/api/v1/health`)
- `GET /`: Full system diagnostic check
- `GET /liveness`: Kubernetes container liveness probe
- `GET /readiness`: Load balancer DB/Redis readiness check

### Attendance (`/api/v1/attendance`)
- `POST /sessions`: Create attendance session
- `POST /mark`: Student self-marks attendance via QR token & geofence
- `GET /reports`: View class attendance reports

### AI Notes & Summarizer (`/api/v1/notes`)
- `POST /upload`: Upload PDF/DOCX/PPTX/TXT document
- `POST /{id}/summarize`: Generate AI summary & key points
- `GET /{id}/summary`: Retrieve summary

### AI Doubt Chatbot RAG (`/api/v1/chat`)
- `POST /sessions`: Create RAG chat session
- `POST /sessions/{id}/message`: Send prompt with streaming response

### AI Assignment Checker (`/api/v1/assignments`)
- `POST /`: Create assignment with rubric
- `POST /{id}/submit`: Student uploads assignment work
- `GET /submission/{id}/review`: Teacher reviews AI evaluation feedback
- `POST /submission/{id}/approve`: Teacher approves/overrides grade

### AI Quiz Generator (`/api/v1/quizzes`)
- `POST /generate`: AI generates quiz from notes/topic across Bloom's Taxonomy
- `POST /{id}/start`: Student starts quiz attempt
- `POST /attempt/{id}/submit`: Submit attempt & run instant auto-grading
- `GET /adaptive-recommendations`: Get student weak area recommendations
- `GET /{id}/leaderboard`: View course leaderboard

### Dashboards & Analytics (`/api/v1/dashboards` & `/api/v1/analytics`)
- `GET /dashboards/student`: Student dashboard
- `GET /dashboards/teacher`: Teacher dashboard
- `GET /dashboards/admin`: Admin system dashboard
- `GET /analytics/attendance`: Recharts attendance trend series

### Reporting Engine (`/api/v1/reports`)
- `POST /generate`: Generate PDF, Excel, or CSV report file
- `GET /{id}/download`: Download generated report file
