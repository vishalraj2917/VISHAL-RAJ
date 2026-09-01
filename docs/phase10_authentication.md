# Phase 10: User Authentication, Accounts & Security

## 1. Overview
Phase 10 implements a complete, enterprise-grade authentication and user account subsystem for the AI Air Quality Prediction System. It enforces secure registration, bcrypt password hashing, JWT Bearer token authentication, user profile management, password updates, and complete prediction history and analytics isolation across accounts.

---

## 2. Security & Account Architecture

```text
       Browser Client (React / Vite)
                   │
                   ▼  (JWT Bearer Header: "Authorization: Bearer <token>")
         FastAPI Auth & API Layer
  ┌────────────────┼──────────────────────────────┐
  │                │                              │
  ▼                ▼                              ▼
/api/auth/*     /api/users/*             /api/predictions/*
(Register/Login) (Profile/Password)   (Strict User Isolation)
  │                │                              │
  └────────────────┴──────────────┬───────────────┘
                                  ▼
                        PostgreSQL 17 Database
                 (users, predictions.user_id, alerts)
```

---

## 3. Core Capabilities

### 1. Registration & Password Security (`POST /api/auth/register`)
- Validates password complexity: minimum 8 characters, at least one uppercase letter, one lowercase letter, and one number.
- Bcrypt salted password hashing with truncation protection (up to 72 bytes).
- Prevents account enumeration and email duplication conflicts.

### 2. Login & JWT Authentication (`POST /api/auth/login`)
- Verifies credentials and generates signed JWT tokens with configured expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Never returns `hashed_password` to clients.

### 3. User Data Isolation (`GET /api/predictions/history`, `GET /api/analytics/*`)
- Predictions generated while authenticated automatically record `user_id`.
- History and analytics endpoints scope queries to the authenticated user's records, completely preventing cross-tenant access.

### 4. User Profile & Password Update (`PUT /api/users/me`, `POST /api/users/change-password`)
- Secure update of user full names and verification-backed password changing.

---

## 4. Frontend Integration

- **`AuthContext.jsx`**: Global React context managing session state, authentication tokens, and automatic re-authorization.
- **`LoginModal.jsx`**, **`RegisterModal.jsx`**, **`ProfileModal.jsx`**: Glassmorphic modals matching the system's design language.
- **Axios Interceptor**: Automatically attaches `Authorization: Bearer <token>` to all protected backend calls.

---

## 5. Verification & Test Suite

- **Pytest Suite**: **61/61 PASSED** (including 8 Phase 10 authentication and user isolation tests in `backend/tests/test_auth.py`).
- **Frontend Build**: `npm run build` completed with **0 errors**.
- **Alembic Migration**: `ae0f4850fca9` successfully applied to PostgreSQL.
