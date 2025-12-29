# Hybrid Authentication Strategy Evaluation

**Goal**: Enable secure local access for electricians (admin/password) while supporting seamless cloud access via reverse proxy (external auth service).

## Requirements

1. **Local Access**: Offline-capable login using a locally stored admin password.
2. **Cloud Access**: Zero-trust approach; the application trusts the authentication performed by an upstream cloud service (e.g., via Headers).
3. **Modern UI**: Backend must support a modern web app (SPA/PWA) built with `shadcn/ui`.

---

## Solution 1: "Dual-Mode" Application Middleware

The application backend implements a middleware that accepts *either* a session/token from a local login *or* trusted headers from the cloud proxy.

### Architecture

- **Backend**: FastAPI generic middleware.
- **Local Flow**: User POSTs credentials to `/api/login` -> Backend issues JWT (set in HTTPOnly Cookie). Middleware validates JWT.
- **Cloud Flow**: Reverse proxy authenticates user, then injects headers (e.g., `X-Auth-User`, `X-Auth-Role`) into the request to the backend. Middleware checks for these headers.

### Pros

- **Simplicity**: Logic resides entirely in the app; single source of truth.
- **Flexibility**: Easy to switch logic based on config (`TRUST_PROXY_HEADERS=True`).
- **Granularity**: Backend knows exactly who is logged in (User vs Cloud Admin).

### Cons

- **Security Risk**: If `TRUST_PROXY_HEADERS` is accidentally enabled locally without a firewall/proxy, anyone can spoof headers. Requires careful network config (firewall to drop external traffic to raw port).

### Verdict

**Recommended**: Best balance of complexity and functionality for a "monolithic" Python app.

---

## Solution 2: Local Sidecar Proxy (The "Adapter" Pattern)

Local access is treated as just another "Cloud" provider. A small nginx/proxy container sits next to the app locally.

### Architecture

- **Backend**: *Only* accepts Trusted Headers. Does not handle passwords.
- **Local Flow**: User hits `local-nginx` -> `local-nginx` presents a basic auth prompt or simple login form -> validates against a htpasswd file -> injects headers -> forwards to Backend.
- **Cloud Flow**: Cloud Proxy -> Backend (Injects headers).

### Pros

- **Security**: Backend code is extremely simple (no password hashing, no login routes).
- **Consistency**: App treats all requests exactly the same.

### Cons

- **Operational Complexity**: Two containers needed locally (Backend + Nginx Sidecar).
- **UI Experience**: "Basic Auth" is ugly. Custom login form in Nginx is harder to maintain/theme than a React page.

---

## Solution 3: OAuth2 / OIDC Gateway

The app acts as an OAuth2 Resource Server.

### Architecture

- **Backend**: Validates Bearer Tokens (JWTs).
- **Local Flow**: A local lightweight IdP (e.g., a simple custom mock-IdP or Dex) issues tokens.
- **Cloud Flow**: Cloud IdP issues tokens.

### Pros

- **Standardization**: Industry standard protocol.
- **Scalability**: Highly scalable if moving to microservices.

### Cons

- **Overkill**: Too complex for a Raspberry Pi "Home Assistant-style" single user setup.
- **Setup**: Requires complex redirect URLs and OIDC configuration.

---

## Recommended approach: Solution 1 (Dual-Mode Middleware)

We will implement **Solution 1** because it keeps the deployment footprint small (single container) while allowing the modern React/shadcn UI to control the login experience completely.

### Implementation Details for Solution 1

1. **Env Var**: `AUTH_METHOD` ("local", "hybrid", "header").
2. **Trusted Header**: `X-Forwarded-User` or custom `X-Onetime-Admin`.
3. **Local Auth**: `bcrypt` hash stored in `station_configurations` or a new `users` table.
4. **Frontend**:
    - If Cloud: App detects headers/config and skips login screen.
    - If Local: Login screen shown.
