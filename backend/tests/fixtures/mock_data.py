"""
Mock data fixtures for backend tests
"""

from typing import List, Dict, Any
from datetime import datetime

# Mock user profiles
MOCK_USERS = {
    "user1": {
        "id": "user-123-456-789",
        "email": "ahmet@test.com",
        "first_name": "Ahmet",
        "last_name": "Yılmaz",
        "created_at": "2025-01-01T10:00:00Z",
    },
    "user2": {
        "id": "user-987-654-321",
        "email": "zeynep@test.com",
        "first_name": "Zeynep",
        "last_name": "Kaya",
        "created_at": "2025-01-02T10:00:00Z",
    },
}

# Mock universities
MOCK_UNIVERSITIES = [
    {
        "id": "uni-001",
        "name": "Massachusetts Institute of Technology",
        "short_name": "MIT",
        "country": "USA",
        "city": "Cambridge",
        "tuition_usd": 55000,
        "programs": ["Computer Science", "Engineering", "Physics"],
        "requirements": {
            "gpa_min": 3.5,
            "toefl_min": 100,
            "ielts_min": 7.5,
        },
        "ranking": 1,
    },
    {
        "id": "uni-002",
        "name": "University of Oxford",
        "short_name": "Oxford",
        "country": "UK",
        "city": "Oxford",
        "tuition_usd": 45000,
        "programs": ["Computer Science", "Mathematics", "Philosophy"],
        "requirements": {
            "gpa_min": 3.7,
            "toefl_min": 110,
            "ieltsMin": 7.5,
        },
        "ranking": 2,
    },
    {
        "id": "uni-003",
        "name": "Technical University of Munich",
        "short_name": "TUM",
        "country": "Germany",
        "city": "Munich",
        "tuition_usd": 0,
        "programs": ["Computer Science", "Engineering", "Data Science"],
        "requirements": {
            "gpa_min": 3.0,
            "toefl_min": 88,
            "ielts_min": 6.5,
        },
        "ranking": 15,
    },
]

# Mock chat messages
MOCK_CHAT_MESSAGES = [
    {
        "id": "msg-001",
        "chat_id": "chat-001",
        "user_id": "user-123-456-789",
        "role": "user",
        "content": "What are the best universities for Computer Science in the USA?",
        "created_at": "2025-01-01T10:00:00Z",
    },
    {
        "id": "msg-002",
        "chat_id": "chat-001",
        "user_id": "user-123-456-789",
        "role": "assistant",
        "content": "Based on rankings, MIT, Stanford, and Carnegie Mellon are top choices.",
        "created_at": "2025-01-01T10:00:05Z",
        "sources": [
            {"id": "uni-001", "title": "MIT Computer Science", "url": "#"}
        ],
    },
]

# Mock documents
MOCK_DOCUMENTS = [
    {
        "document_id": "doc-001",
        "user_id": "user-123-456-789",
        "file_name": "transcript.pdf",
        "file_size": 102400,
        "doc_type": "transcript",
        "upload_path": "uploads/user-123/transcript.pdf",
        "uploaded_at": "2025-01-01T09:00:00Z",
        "status": "processed",
    },
    {
        "document_id": "doc-002",
        "user_id": "user-123-456-789",
        "file_name": "diploma.pdf",
        "file_size": 153600,
        "doc_type": "diploma",
        "upload_path": "uploads/user-123/diploma.pdf",
        "uploaded_at": "2025-01-01T09:30:00Z",
        "status": "processed",
    },
]

# Mock LLM responses for testing
MOCK_LLM_RESPONSES = {
    "university_question": {
        "question": "What are the best universities for CS in the UK?",
        "answer": "Based on rankings and reputation, Imperial College London, University of Oxford, and University of Cambridge are among the best universities for Computer Science in the UK. Imperial is particularly known for its strong industry connections, while Oxford and Cambridge have centuries of academic excellence.",
        "sources": ["uni-002"],
        "confidence": 0.92,
    },
    "visa_question": {
        "question": "What documents do I need for UK student visa?",
        "answer": "For a UK student visa, you will need:\n1. CAS (Confirmation of Acceptance for Studies) letter from your university\n2. Valid passport\n3. Proof of funds (tuition + living expenses)\n4. TB test certificate (if from listed countries)\n5. Academic transcripts and certificates\n6. English language test results (IELTS/TOEFL)",
        "sources": ["doc-visa-uk-001"],
        "confidence": 0.88,
    },
    "tuition_question": {
        "question": "How much does MIT cost per year?",
        "answer": "MIT's tuition for the 2024-2025 academic year is approximately $55,000 per year. Including room, board, and other expenses, the total cost of attendance is around $80,000-$85,000 per year. However, MIT has excellent financial aid and meets 100% of demonstrated need for all students.",
        "sources": ["uni-001"],
        "confidence": 0.95,
    },
}

# Mock vector embeddings (simplified)
import numpy as np


def generate_mock_embedding(dimension: int = 1536, seed: int = 42) -> List[float]:
    """Generate deterministic mock embedding vector"""
    np.random.seed(seed)
    return np.random.rand(dimension).tolist()


# Sample document chunks for RAG testing
MOCK_DOCUMENT_CHUNKS = [
    {
        "chunk_id": "chunk-001",
        "document_id": "doc-rag-001",
        "content": "MIT's Computer Science program is ranked #1 in the world. The program offers courses in AI, machine learning, systems, and theory.",
        "metadata": {
            "source": "MIT CS Department",
            "page": 1,
            "chunk_index": 0,
        },
        "embedding": generate_mock_embedding(seed=1),
    },
    {
        "chunk_id": "chunk-002",
        "document_id": "doc-rag-002",
        "content": "Oxford University requires a minimum IELTS score of 7.5 for international students. The application deadline is typically in October.",
        "metadata": {
            "source": "Oxford Admissions",
            "page": 2,
            "chunk_index": 1,
        },
        "embedding": generate_mock_embedding(seed=2),
    },
    {
        "chunk_id": "chunk-003",
        "document_id": "doc-rag-003",
        "content": "German universities like TUM offer tuition-free education for international students. However, students must prove they have sufficient funds for living expenses.",
        "metadata": {
            "source": "Study in Germany Guide",
            "page": 5,
            "chunk_index": 2,
        },
        "embedding": generate_mock_embedding(seed=3),
    },
]

# Sample PDF content for conversion testing
SAMPLE_PDF_CONTENT = """
# University of Example

## Computer Science Program

### Program Overview
The Computer Science program at University of Example offers a comprehensive curriculum covering:
- Artificial Intelligence
- Machine Learning
- Software Engineering
- Computer Systems

### Admission Requirements
- Minimum GPA: 3.5/4.0
- TOEFL: 100 (iBT)
- IELTS: 7.0

### Tuition and Fees
Annual tuition: $45,000
Living expenses: $15,000 estimated

### Application Deadline
Fall semester: January 15
Spring semester: September 15
"""

# Mock HTML for web scraping tests
MOCK_UNIVERSITY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MIT Computer Science</title>
</head>
<body>
    <h1>MIT Computer Science Department</h1>
    <div class="program-info">
        <h2>Program Information</h2>
        <p>The MIT Computer Science program is world-renowned.</p>
    </div>
    <div class="requirements">
        <h2>Admission Requirements</h2>
        <ul>
            <li>GPA: Minimum 3.7</li>
            <li>GRE: Required</li>
            <li>TOEFL: Minimum 100</li>
        </ul>
    </div>
    <div class="tuition">
        <h2>Tuition</h2>
        <p>Annual tuition: $55,000</p>
    </div>
</body>
</html>
"""
