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

## LLM Evaluation Framework

The project includes a comprehensive evaluation framework for assessing the quality and accuracy of the chatbot's responses.

### Features
- **Factual Accuracy**: Validates correctness of information and required keywords
- **Groundedness**: Ensures answers are based on retrieved documents (prevents hallucinations)
- **Relevance**: Checks if answers address the user's question

### Quick Start

```bash
# Navigate to backend
cd backend/src

# Run demo (no dependencies required)
python -m evaluation.demo

# List available test datasets
python -m evaluation.run_evaluation --list-datasets

# Run evaluation on a dataset
python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual
```

### Documentation
- **Quick Start**: `backend/src/evaluation/QUICKSTART.md` - 5-minute setup guide
- **Full Documentation**: `backend/src/evaluation/README.md` - Complete guide
- **Technical Details**: `backend/src/evaluation/IMPLEMENTATION_SUMMARY.md`

### Creating Custom Test Cases

Test cases are defined in JSON format in `backend/src/evaluation/datasets/`. Each test case includes:
- Question and expected answer
- Ground truth data
- Evaluation metrics with thresholds
- Good and bad answer examples

See `backend/src/evaluation/datasets/tum_informatics_deadlines_factual.json` for a complete example.

For more details, see the [Evaluation Framework Documentation](backend/src/evaluation/README.md).