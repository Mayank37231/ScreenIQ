# ScreenIQ

ScreenIQ is a lightweight HR screening tool with a Django REST API, JWT authentication, PostgreSQL storage, and a Next.js App Router frontend. Users paste a job description and resume, receive a streamed AI score with three reasons, and review past screenings from a paginated dashboard.

## Setup Guide

### Backend

```bash
docker compose up -d postgres
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The default `AI_PROVIDER=mock` makes the app runnable without an AI key. To use OpenAI, set `AI_PROVIDER=openai`, add `OPENAI_API_KEY`, and choose an `OPENAI_MODEL`.

Get a JWT access token:

```bash
curl -X POST http://localhost:8000/api/token/ -H "Content-Type: application/json" -d "{\"username\":\"YOUR_USER\",\"password\":\"YOUR_PASSWORD\"}"
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000/screen`, paste the JWT access token, then submit screenings. The dashboard is at `http://localhost:3000/dashboard`.

## Bugs Fixed

- Unsafe request access: the starter used `request.data['job_description']` and `request.data['resume']`, which throws `KeyError` and returns a 500 for malformed input. I replaced it with `ScreenCandidateSerializer`, so missing or blank fields return clear 400 validation errors.
- Missing authentication: the screening endpoint created rows with `request.user` but did not require an authenticated user. I added `IsAuthenticated`, matching the JWT requirement and preventing anonymous writes.
- Deprecated/fragile OpenAI call shape: the starter used the older `openai.ChatCompletion.create` style. The implementation uses the current `OpenAI` client when `AI_PROVIDER=openai`.
- Prompt ignored the job description: the starter scored only the resume, making the output unreliable. The new prompt compares both job description and resume.
- Unstructured score storage: the starter saved raw model text into `ai_score`, making values like `7.3`, `Seven`, and long prose hard for the UI to render. The backend now normalizes to a decimal score and stores reasons separately.
- Incorrect success status: the starter returned `200 OK` after creating a new row. The fixed endpoint returns `201 Created`.
- Data leakage in application list: the starter used `Application.objects.all()`, exposing every user's screenings. The list and detail views now filter by `created_by=request.user`.

Short comments describing these fixes are also included directly in `backend/applications/views.py`.

## AI Prompt Design

The screening prompt uses a system message to constrain the model to job-relevant evidence and explicitly ignore protected or proxy attributes. The user message includes both the job description and resume, asks for strict JSON, and requires a `1-10` score plus exactly three concise reasons. JSON output keeps parsing deterministic, while the reasons force the model to expose fit, gaps, and evidence rather than returning a bare number.

## Security Vulnerability

The vulnerable code returned `Application.objects.all()` to any authenticated user, which is an object-level authorization flaw. In HR software this could expose resumes, scores, and screening notes across teams or tenants. The fix filters every list and detail query by `created_by=request.user`, so users can only access applications they created.

## Frontend State Management

I used local React state with `useState` because the form, streaming text, token input, and selected dashboard row are page-local concerns. A global store would add complexity without solving a real sharing problem here; if the app later adds full auth flows, shared filters, or cross-page candidate workflows, a small context or query cache would become more useful.

## Dashboard Pagination

The dashboard uses server-side pagination with a page size of 50. This keeps the API payload and DOM small for 500+ rows, avoids rendering lag, and works well when the dataset grows beyond what the browser should hold. Virtual scrolling can feel smoother for already-loaded data, but it still requires careful API windowing for large or sensitive HR records, so server pagination is the simpler and safer tradeoff.

## Score Normalisation

AI score normalization happens in the backend in `applications/ai.py`. This handles decimals like `7.3`, words like `Seven`, and prose containing a score before persisting the result. I chose the backend because the API contract should be stable for all clients, tests can cover it once, and the database should not store inconsistent score formats.

## Streaming Choice

The app streams with Server-Sent Events from Django using `StreamingHttpResponse`. SSE is a good fit because screening output is one-way from server to browser, simpler than WebSockets, and easy to consume from `fetch` streams in the Next.js page. The backend streams model chunks progressively and then sends a final `complete` event containing the saved application.

## Tests

Minimum critical tests are in `backend/applications/tests.py`:

This test file verifies that the AI screening API works correctly, securely, and consistently.
It uses Django REST Framework’s testing utilities to test:

score normalization
authenticated API behavior
database creation
user-based data isolation
validation errors

- Score normalization covers decimal and word outputs, which addresses inconsistent AI responses.
- Screening creation verifies the endpoint saves a row for the authenticated user and derives a candidate name.
- Application listing verifies one user cannot see another user's screenings.

Run them with:

```bash
cd backend
set USE_SQLITE_FOR_TESTS=true
python manage.py test
```

## Bias & Fairness

I would detect bias with a mix of controlled tests and production monitoring. First, create paired resume evaluations where the skills and experience are identical but names, universities, locations, and other proxy attributes are varied. The expected result is score stability; meaningful score movement would indicate bias or proxy sensitivity. I would also analyze historical screenings by cohort, controlling for job family, years of experience, required skills, and recruiter decisions, then look for unexplained score differences across demographic proxies where legally and ethically permitted.

To reduce bias, I would change both product design and model behavior. The prompt already instructs the model to evaluate only job-relevant evidence and ignore protected or proxy traits. Beyond prompting, I would redact or transform sensitive fields before model evaluation, separate candidate identity from scoring, and use structured rubrics tied to explicit job requirements. I would keep humans in the loop, show the reasons behind each score, and make scores advisory rather than automatic rejection criteria. Finally, I would run regular bias audits after model or prompt changes, log model versions and prompts for traceability, and establish an escalation path when candidates or recruiters dispute an AI-generated recommendation.
