"""
Application Letters router - AI-powered letter analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
import json
import re
import asyncio
from core.models import CamelCaseModel
from core.dependencies import get_current_user
from db.lib.core import supabase
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter(
    prefix="/letters",
    tags=["letters"]
)

# Global reference to RAG pipeline (set by main.py)
rag_pipeline = None


def set_rag_pipeline(pipeline):
    """Set the RAG pipeline reference for AI analysis."""
    global rag_pipeline
    rag_pipeline = pipeline


# ============= REQUEST/RESPONSE MODELS =============

class HighlightRange(CamelCaseModel):
    start: int
    end: int


class AISuggestion(CamelCaseModel):
    id: str
    category: str  # grammar, tone, structure, program-alignment
    severity: str  # info, warning, success
    title: str
    description: str
    suggestion: str
    replacement: Optional[str] = None  # The exact text to replace the highlighted portion
    highlight_range: Optional[HighlightRange] = None


class LetterAnalysisRequest(CamelCaseModel):
    content: str
    program_slug: Optional[str] = None


class LetterAnalysisResponse(CamelCaseModel):
    suggestions: List[AISuggestion]
    word_count: int
    analysis_metadata: Optional[Dict[str, Any]] = None


# ============= ANALYSIS ENDPOINT =============

@router.post("/analyze", response_model=LetterAnalysisResponse)
async def analyze_letter(
    request: LetterAnalysisRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Analyze an application letter and provide AI-powered suggestions.
    
    Uses the RAG system to retrieve program-specific requirements and
    the LLM to generate contextual writing feedback.
    """
    if not rag_pipeline:
        raise HTTPException(503, "RAG pipeline not initialized")
    
    content = request.content.strip()
    if not content:
        return LetterAnalysisResponse(
            suggestions=[],
            word_count=0,
            analysis_metadata={"error": "Empty content"}
        )
    
    # Calculate word count
    word_count = len(content.split())
    
    try:
        # 1. Get program-specific context if program_slug is provided
        program_context = ""
        if request.program_slug:
            try:
                # Use RAG to retrieve program requirements
                query = f"admission requirements application process {request.program_slug}"
                query_embedding = rag_pipeline.retriever_pipeline.embeddings.embed_query(query)
                
                from rag.chatbot.db_ops import retrieve_chunks
                program_docs = retrieve_chunks(
                    query=query,
                    query_embedding=query_embedding,
                    top_k=5,
                    similarity_threshold=0.35
                )
                
                if program_docs:
                    program_context = "\n\n".join([
                        f"Program Info {i+1}:\n{doc['content']}"
                        for i, doc in enumerate(program_docs)
                    ])
            except Exception as e:
                print(f"Error retrieving program context: {e}")
                program_context = ""
        
        # 2. Get user profile for personalization
        user_profile = ""
        try:
            # Fetch user basic info
            user_data = supabase.table("users")\
                .select("first_name, last_name, applicant_type")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            if user_data.data:
                user_profile = f"User: {user_data.data.get('first_name', '')} {user_data.data.get('last_name', '')}\n"
                user_profile += f"Applicant type: {user_data.data.get('applicant_type', 'unknown')}\n"
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
        
        # 3. Construct specialized prompt for letter analysis
        system_prompt = """You are an application letter reviewer for TUM university admissions.

Analyze the letter and return ONLY a JSON object with suggestions.

Check for:
1. Wrong program/university name mentioned (CRITICAL)
2. Spelling and grammar errors
3. Unclear or informal language
4. Weak program alignment
5. Missing qualifications

For each issue provide:
- category: "critical", "grammar", "tone", "structure", "program-alignment"
- severity: "critical" (wrong program), "warning" (errors), "info" (improvements)
- title: Short description
- description: What's wrong
- suggestion: How to fix it
- originalText: EXACT text from letter with the issue (5-10+ words for context)
- replacement: Corrected text (only for grammar/spelling fixes, null otherwise)

IMPORTANT PROGRAM NAME MATCHING:
- Different variations of the same program name are ACCEPTABLE (e.g., "Informatics Bachelor", "Bachelor of Informatics", "Informatics BSc", "Informatics Bachelor of Science")
- ONLY flag as critical if the applicant mentions a COMPLETELY DIFFERENT program (e.g., writing about "Mathematics" when applying to "Informatics")
- Shortened or alternative versions of the correct program name are NOT errors

CRITICAL: 
- If wrong program mentioned, return originalText with the COMPLETE sentence containing wrong name
- For spelling errors, include full word + surrounding words
- Return ONLY valid JSON, no extra text

{"suggestions": [...]}
"""

        # Build user message parts
        program_context_text = f"PROGRAM CONTEXT (for reference only, do not analyze):\n{program_context}\n\n" if program_context else ""
        user_profile_text = f"USER PROFILE (metadata only, do not analyze):\n{user_profile}\n\n" if user_profile else ""
        
        user_message = f"""Please analyze this application letter:

{program_context_text}{user_profile_text}APPLICATION LETTER TO ANALYZE ({word_count} words):
--- START OF LETTER ---
{content}
--- END OF LETTER ---

TARGET PROGRAM: {request.program_slug}

IMPORTANT: Only analyze the text between "START OF LETTER" and "END OF LETTER" markers.
Do NOT analyze the PROGRAM CONTEXT or USER PROFILE sections above - these are metadata for your reference.

Analyze this letter comprehensively. Pay special attention to:
1. Is the applicant writing about the CORRECT program ({request.program_slug})?
2. Are there any factual errors about the program or university?
3. Does the letter demonstrate genuine knowledge of and fit for this specific program?

Provide specific, actionable suggestions prioritized by importance."""

        # 4. Call LLM for analysis asynchronously
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: rag_pipeline.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ], temperature=0.3, max_tokens=2048)
        )
        
        # 5. Parse LLM response
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        # Try to extract JSON from response
        suggestions = []
        try:
            # Try direct JSON parse
            parsed = json.loads(response_content)
            suggestions_data = parsed.get("suggestions", [])
        except json.JSONDecodeError:
            # Try to find JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
                suggestions_data = parsed.get("suggestions", [])
            else:
                # Try to find any JSON object
                json_match = re.search(r'\{.*"suggestions".*\}', response_content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    suggestions_data = parsed.get("suggestions", [])
                else:
                    raise ValueError("Could not parse JSON from LLM response")
        
        # 6. Convert to AISuggestion models
        for i, sug in enumerate(suggestions_data[:15]):  # Limit to 15 suggestions
            try:
                # Build highlight range by finding the original text in content
                highlight_range = None
                original_text = sug.get("originalText")
                
                if original_text and isinstance(original_text, str):
                    # Find the text in the content
                    start_pos = content.find(original_text)
                    if start_pos >= 0:
                        highlight_range = HighlightRange(
                            start=start_pos,
                            end=start_pos + len(original_text)
                        )
                        print(f"[Analysis] ✓ Found '{original_text[:50]}...' at position {start_pos}-{start_pos + len(original_text)}")
                    else:
                        # Try case-insensitive search as fallback
                        lower_content = content.lower()
                        lower_original = original_text.lower()
                        start_pos = lower_content.find(lower_original)
                        if start_pos >= 0:
                            highlight_range = HighlightRange(
                                start=start_pos,
                                end=start_pos + len(original_text)
                            )
                            print(f"[Analysis] ✓ Found (case-insensitive) '{original_text[:50]}...' at position {start_pos}-{start_pos + len(original_text)}")
                        else:
                            print(f"[Analysis] ✗ Could not find: '{original_text[:100]}'")
                            print(f"[Analysis]   Content preview: '{content[:200]}'")
                
                suggestion = AISuggestion(
                    id=f"ai-{i+1}",
                    category=sug.get("category", "info"),
                    severity=sug.get("severity", "info"),
                    title=sug.get("title", "Suggestion"),
                    description=sug.get("description", ""),
                    suggestion=sug.get("suggestion", ""),
                    replacement=sug.get("replacement"),
                    highlight_range=highlight_range
                )
                suggestions.append(suggestion)
            except Exception as e:
                print(f"Error parsing suggestion {i}: {e}")
                continue
        
        return LetterAnalysisResponse(
            suggestions=suggestions,
            word_count=word_count,
            analysis_metadata={
                "program_slug": request.program_slug,
                "has_program_context": bool(program_context),
                "has_user_profile": bool(user_profile),
                "total_suggestions": len(suggestions)
            }
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Analysis failed: {str(e)}")
