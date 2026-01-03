# teduco-ai

Description
Teduco is a genAI-powered education consultation tool designed to help turkish students navigate the complexities of international education through reliable Q&A, application guidance, and personalized planning. The system provides an accessible, affordable, and trustworthy alternative to traditional consultancy services.

Core Features (Use Cases)
International Education Q&A Chatbot: Allow users to ask detailed questions about study abroad options, university requirements, tuition fees, and scholarship opportunities.

Verified Information Retrieval: Provide answers sourced and verified from a curated database of universities, and other official institutions to ensure reliability.

Personalized University Matching (Basic): Suggest potential countries and universities based on the student's academic profile, field of interest, and stated budget.

Optional Features
Document Analysis: AI-powered review and feedback on application materials, such as cover letters, statements of purpose, and resumes.

Application Organizer and Tracker: A comprehensive dashboard to manage all aspects of the application process, from document submission to follow-ups.

Calendar Sync: Integrate application deadlines and reminders into Google, Apple, or Microsoft calendars.

LLM API Integration
Use LLMs for advanced conversational Q&A, understanding complex user intent and nuanced queries about international education.

Employ Retrieval-Augmented Generation (RAG) to query the curated database (universities, official sites) to provide trustworthy and cited answers.

Generate personalized application checklists and timelines based on user goals and chosen universities.

Incorporate memory-based user modeling to provide personalized follow-ups and guidance throughout the long application cycle. (Optional)

Test Data or Input Sources
Publicly available data scraped and indexed from international university websites (admission requirements, program details, fees).

Official documentation from government agencies regarding student visa and immigration policies (e.g., embassy websites, official education portals).

Data from recognized educational institutions and scholarship funds.

Synthetic datasets of common student questions and conversational flows in both Turkish and English.

Anonymized sample student profiles for testing recommendation of study programs.

Expected Outcome
A genAI-powered consulting chatbot (web app). The tool should demonstrate how generative AI can make international education consulting accessible, affordable, and trustworthy by providing verified, personalized guidance and automating complex application logistics for students.

---

## Development

### Running Tests

Teduco-AI has a comprehensive test suite covering frontend, backend, and end-to-end functionality. See [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) for detailed testing documentation.

#### Frontend Tests

```bash
cd frontend

# Unit tests (Vitest)
npm run test              # Watch mode
npm run test:coverage     # With coverage report

# E2E tests (Playwright)
npm run test:e2e          # Headless mode
npm run test:e2e:ui       # With UI
npx playwright show-report  # View latest report
```

#### Backend Tests

```bash
cd backend

# All tests
pytest

# Specific test types
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest -m rag               # RAG-specific tests
pytest -m "not slow"        # Skip slow tests

# With coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html     # View coverage report
```

#### E2E Tests (Full Stack)

```bash
# Start services with Docker Compose
docker-compose up -d

# Wait for services to be ready
npx wait-on http://localhost:3000 http://localhost:8000

# Run E2E tests
cd frontend
npx playwright test

# View results
npx playwright show-report
```

### CI/CD

Tests run automatically on:
- Every push to `main` or `develop` branches
- Every pull request
- Manual trigger via GitHub Actions

View test results: **Actions** → **Test Suite** workflow

### Architecture Documentation

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system architecture and development guidelines.

### Testing Strategy

See [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) for comprehensive testing guidelines, tools, and best practices.