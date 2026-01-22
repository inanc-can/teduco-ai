"""
Register test users, complete onboarding, upload documents, and test chatbot.
"""
import os
import json
import time
import requests
from datetime import datetime
from supabase import create_client

# Configuration
SUPABASE_URL = "https://ddljivtgmjplsejjvjyr.supabase.co"
SUPABASE_KEY = "sb_publishable_x1u1JRd1A1OYgiWMDvWVzg_VLejVtN6"
SUPABASE_SERVICE_KEY = "sb_secret_KW40HDLaq785KP6JuzhIcg_lpxamkDX"
BACKEND_URL = "http://localhost:8000"
BUCKET_NAME = "user-documents"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Test user configurations
TEST_USERS = [
    {
        "folder": "elif_yilmaz",
        "email": "elif.yilmaz.test@gmail.com",
        "password": "TestPassword123!",
        "profile": {
            "firstName": "Elif",
            "lastName": "Yilmaz",
            "phone": "+90 532 123 4567",
            "applicantType": "high_school",
            "desiredCountries": ["Germany"],
            "desiredFields": ["Computer Science"],
            "targetPrograms": ["Bachelor's"],
            "preferredIntake": "Fall 2025",
            "currentCity": "Istanbul, Turkey",
            "highSchoolName": "Istanbul Erkek Lisesi",
            "gpa": "92",
            "gpaScale": "100",
            "gradYear": "2025",
            "yksPlacement": True,
            "extracurriculars": "President of Game Development Club, Global Game Jam 2024 participant, 2nd place National High School Programming Competition",
            "scholarshipInterest": True,
            "additionalNotes": "Passionate about game development, specifically Unity and Unreal Engine"
        },
        "documents": [
            {"path": "student_documents/high_school_transcript.pdf", "type": "transcript"},
            {"path": "student_documents/cv.pdf", "type": "cv"}
        ],
        "test_questions": [
            "I'm interested in game development and want to study computer science in Germany. What programs would you recommend for me at TUM?",
            "What are the admission requirements for the Informatics Bachelor program? Do I need to know German?",
            "When should I apply for Fall 2025 intake?"
        ]
    },
    {
        "folder": "ahmet_ozturk",
        "email": "ahmet.ozturk.test@gmail.com",
        "password": "TestPassword123!",
        "profile": {
            "firstName": "Ahmet",
            "lastName": "Ozturk",
            "phone": "+90 533 987 6543",
            "applicantType": "university",
            "desiredCountries": ["Germany"],
            "desiredFields": ["Computer Science"],
            "targetPrograms": ["Master's"],
            "preferredIntake": "Fall 2025",
            "currentCity": "Ankara, Turkey",
            "universityName": "Middle East Technical University (METU)",
            "universityProgram": "Computer Engineering",
            "universityGpa": "3.45",
            "creditsCompleted": "210",
            "expectedGraduation": "2025-06-15",
            "studyMode": "full-time",
            "researchFocus": "Game AI, Procedural Content Generation, Computer Graphics",
            "portfolioLink": "https://github.com/ahmetozturk-gamedev",
            "additionalNotes": "Thesis on Procedural Dungeon Generation Using ML. TA for Computer Graphics. Published at Turkish Game Dev Conference 2024."
        },
        "documents": [
            {"path": "student_documents/university_transcript.pdf", "type": "transcript"},
            {"path": "student_documents/cv.pdf", "type": "cv"}
        ],
        "test_questions": [
            "I'm finishing my Computer Engineering degree and I'm really passionate about game development, especially game AI. What master's programs at TUM would be best for me?",
            "What do I need to apply for the Games Engineering Master's program? Is my GPA of 3.45 competitive?",
            "I graduate in June 2025. Is that too late for Fall 2025 intake?"
        ]
    },
    {
        "folder": "zeynep_kaya",
        "email": "zeynep.kaya.test@gmail.com",
        "password": "TestPassword123!",
        "profile": {
            "firstName": "Zeynep",
            "lastName": "Kaya",
            "phone": "+90 535 456 7890",
            "applicantType": "university",
            "desiredCountries": ["Germany"],
            "desiredFields": ["Computer Science", "Engineering"],
            "targetPrograms": ["Master's"],
            "preferredIntake": "Fall 2025",
            "currentCity": "Izmir, Turkey",
            "universityName": "Izmir Institute of Technology (IYTE)",
            "universityProgram": "Mathematics",
            "universityGpa": "3.72",
            "creditsCompleted": "180",
            "expectedGraduation": "2025-01-15",
            "studyMode": "full-time",
            "researchFocus": "Statistical Learning, Machine Learning, Data Visualization",
            "portfolioLink": "https://kaggle.com/zeynepkaya",
            "additionalNotes": "Thesis on Bayesian Methods for High-Dimensional Regression. Minor in Computer Science. Google Data Analytics Certificate."
        },
        "documents": [
            {"path": "student_documents/university_transcript.pdf", "type": "transcript"},
            {"path": "student_documents/cv.pdf", "type": "cv"}
        ],
        "test_questions": [
            "I have a Mathematics degree with focus on statistical learning and machine learning. I want to pursue data science at TUM. What programs are available?",
            "My thesis was on Bayesian methods for high-dimensional regression. Is this relevant for the Data Science master's?",
            "What's the difference between Mathematics MSc and Mathematics in Data Science MSc? Which one is better for me?"
        ]
    }
]

def create_supabase_client(use_service_key=False):
    key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_KEY
    return create_client(SUPABASE_URL, key)

def register_user(email: str, password: str) -> dict:
    """Register a new user via Supabase Auth"""
    supabase = create_supabase_client()
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if response.user:
            print(f"  [OK] Registered user: {email}")
            return {
                "user_id": response.user.id,
                "email": email,
                "access_token": response.session.access_token if response.session else None
            }
        else:
            print(f"  [WARN] Registration returned no user for {email}")
            return None
    except Exception as e:
        if "already registered" in str(e).lower() or "already exists" in str(e).lower():
            print(f"  [INFO] User {email} already exists, attempting login...")
            return login_user(email, password)
        print(f"  [ERROR] Registration failed for {email}: {e}")
        return None

def login_user(email: str, password: str) -> dict:
    """Login existing user"""
    supabase = create_supabase_client()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user and response.session:
            print(f"  [OK] Logged in user: {email}")
            return {
                "user_id": response.user.id,
                "email": email,
                "access_token": response.session.access_token
            }
    except Exception as e:
        print(f"  [ERROR] Login failed for {email}: {e}")
    return None

def complete_onboarding(access_token: str, profile: dict) -> bool:
    """Complete user onboarding via backend API"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/onboarding",
            headers=headers,
            json=profile,
            timeout=30
        )
        if response.status_code in [200, 201]:
            print(f"  [OK] Onboarding completed")
            return True
        else:
            print(f"  [WARN] Onboarding returned {response.status_code}: {response.text[:200]}")
            # Try updating profile instead
            response = requests.put(
                f"{BACKEND_URL}/profile",
                headers=headers,
                json=profile,
                timeout=30
            )
            if response.status_code in [200, 201]:
                print(f"  [OK] Profile updated via PUT")
                return True
            return False
    except Exception as e:
        print(f"  [ERROR] Onboarding failed: {e}")
        return False

def upload_document(access_token: str, user_id: str, doc_path: str, doc_type: str) -> bool:
    """Upload a document to Supabase Storage"""
    full_path = os.path.join(BASE_DIR, doc_path)
    if not os.path.exists(full_path):
        print(f"  [ERROR] Document not found: {full_path}")
        return False

    supabase = create_supabase_client(use_service_key=True)

    try:
        filename = os.path.basename(doc_path)
        storage_path = f"{user_id}/{filename}"

        with open(full_path, "rb") as f:
            file_data = f.read()

        # Upload to storage
        result = supabase.storage.from_(BUCKET_NAME).upload(
            storage_path,
            file_data,
            {"content-type": "application/pdf"}
        )

        print(f"  [OK] Uploaded {filename} to storage")

        # Register in documents table
        doc_record = {
            "user_id": user_id,
            "storage_path": storage_path,
            "doc_type": doc_type,
            "mime_type": "application/pdf",
            "original_filename": filename,
            "file_size": len(file_data)
        }

        supabase.table("documents").insert(doc_record).execute()
        print(f"  [OK] Registered {doc_type} in documents table")
        return True

    except Exception as e:
        if "Duplicate" in str(e) or "already exists" in str(e).lower():
            print(f"  [INFO] Document already exists: {doc_path}")
            return True
        print(f"  [ERROR] Upload failed for {doc_path}: {e}")
        return False

def test_chatbot(access_token: str, questions: list) -> list:
    """Test chatbot with questions and record responses"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    conversations = []
    chat_id = None

    for i, question in enumerate(questions, 1):
        print(f"\n  Question {i}: {question[:60]}...")

        try:
            payload = {"question": question}
            if chat_id:
                payload["chat_id"] = chat_id

            response = requests.post(
                f"{BACKEND_URL}/chat",
                headers=headers,
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No answer")
                chat_id = data.get("chat_id")

                print(f"  Answer: {answer[:150]}...")

                conversations.append({
                    "question": question,
                    "answer": answer,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print(f"  [ERROR] Chat returned {response.status_code}: {response.text[:200]}")
                conversations.append({
                    "question": question,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                })

        except Exception as e:
            print(f"  [ERROR] Chat failed: {e}")
            conversations.append({
                "question": question,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    return conversations

def save_credentials(folder: str, email: str, password: str, user_id: str):
    """Save credentials to file"""
    cred_path = os.path.join(BASE_DIR, folder, "credentials.txt")
    with open(cred_path, "w") as f:
        f.write(f"# {folder.replace('_', ' ').title()} - Test Account Credentials\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"Email: {email}\n")
        f.write(f"Password: {password}\n")
        f.write(f"User ID: {user_id}\n")
    print(f"  [OK] Saved credentials to {cred_path}")

def save_test_results(folder: str, user_id: str, conversations: list):
    """Save test results to JSON"""
    results_path = os.path.join(BASE_DIR, folder, "test_results.json")
    results = {
        "user": folder,
        "user_id": user_id,
        "test_date": datetime.now().isoformat(),
        "conversations": conversations
    }
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  [OK] Saved test results to {results_path}")

def process_user(user_config: dict) -> bool:
    """Process a single test user"""
    folder = user_config["folder"]
    print(f"\n{'='*60}")
    print(f"Processing: {folder}")
    print(f"{'='*60}")

    # Step 1: Register or login
    print("\n[1] Registering/logging in user...")
    auth_result = register_user(user_config["email"], user_config["password"])
    if not auth_result:
        print(f"  [FAILED] Could not authenticate user")
        return False

    user_id = auth_result["user_id"]
    access_token = auth_result["access_token"]

    if not access_token:
        print("  [INFO] No access token, attempting login...")
        auth_result = login_user(user_config["email"], user_config["password"])
        if not auth_result or not auth_result.get("access_token"):
            print(f"  [FAILED] Could not get access token")
            return False
        access_token = auth_result["access_token"]
        user_id = auth_result["user_id"]

    # Save credentials
    save_credentials(folder, user_config["email"], user_config["password"], user_id)

    # Step 2: Complete onboarding
    print("\n[2] Completing onboarding...")
    complete_onboarding(access_token, user_config["profile"])

    # Step 3: Upload documents
    print("\n[3] Uploading documents...")
    for doc in user_config["documents"]:
        doc_path = os.path.join(folder, doc["path"])
        upload_document(access_token, user_id, doc_path, doc["type"])

    # Step 4: Test chatbot
    print("\n[4] Testing chatbot...")
    conversations = test_chatbot(access_token, user_config["test_questions"])

    # Save results
    save_test_results(folder, user_id, conversations)

    print(f"\n[DONE] Completed processing for {folder}")
    return True

def main():
    print("="*60)
    print("TEDUCO-AI Test User Registration and Testing")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Backend: {BACKEND_URL}")
    print(f"Supabase: {SUPABASE_URL}")

    # Check backend health
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"Backend health: {response.json()}")
        else:
            print(f"[WARN] Backend health check failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Cannot reach backend: {e}")
        return

    # Process each user
    results = {}
    for user_config in TEST_USERS:
        success = process_user(user_config)
        results[user_config["folder"]] = "SUCCESS" if success else "FAILED"
        time.sleep(2)  # Brief pause between users

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for user, status in results.items():
        print(f"  {user}: {status}")
    print(f"\nCompleted at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
