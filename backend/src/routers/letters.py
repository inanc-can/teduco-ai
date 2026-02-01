"""
Application Letters router - AI-powered letter analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
import json
import re
import asyncio
import hashlib
from pydantic import BaseModel, Field
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


async def _get_program_context(program_slug: Optional[str]) -> str:
    """Fetch program-specific context from RAG system."""
    if not program_slug or not rag_pipeline:
        return ""
    
    try:
        query = f"admission requirements application process {program_slug}"
        loop = asyncio.get_event_loop()
        
        # Run embedding in executor to avoid blocking
        query_embedding = await loop.run_in_executor(
            None,
            lambda: rag_pipeline.retriever_pipeline.embeddings.embed_query(query)
        )
        
        from rag.chatbot.db_ops import retrieve_chunks
        program_docs = await loop.run_in_executor(
            None,
            lambda: retrieve_chunks(
                query=query,
                query_embedding=query_embedding,
                top_k=3,  # Reduced from 5 for speed
                similarity_threshold=0.4  # Increased threshold for relevance
            )
        )
        
        if program_docs:
            return "\n".join([doc['content'] for doc in program_docs])
        return ""
    except Exception as e:
        print(f"[Analysis] Error retrieving program context: {e}")
        return ""


async def _get_user_profile(user_id: str) -> str:
    """Fetch user profile for personalization."""
    try:
        loop = asyncio.get_event_loop()
        user_data = await loop.run_in_executor(
            None,
            lambda: supabase.table("users")
                .select("first_name, applicant_type")
                .eq("user_id", user_id)
                .single()
                .execute()
        )
        
        if user_data.data:
            first_name = user_data.data.get('first_name', '')
            applicant_type = user_data.data.get('applicant_type', 'unknown')
            return f"User: {first_name}, Type: {applicant_type}"
        return ""
    except Exception as e:
        print(f"[Analysis] Error retrieving user profile: {e}")
        return ""


def _clean_json_string(raw: str) -> str:
    """Best-effort cleanup for malformed JSON from LLMs."""
    # Trim to outermost JSON object
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    # Remove trailing commas before } or ]
    raw = re.sub(r',\s*(\}|\])', r'\1', raw)

    # Remove invalid control characters
    raw = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', raw)

    return raw


def _extract_json_candidate(raw: str) -> Optional[str]:
    """Extract the first balanced JSON object from a string."""
    start = raw.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(raw)):
        ch = raw[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return raw[start:i + 1]
    return None


def _handle_truncated_json(raw: str) -> str:
    """Handle truncated JSON by closing incomplete strings and structures."""
    # Count opening/closing braces and brackets
    open_braces = raw.count('{')
    close_braces = raw.count('}')
    open_brackets = raw.count('[')
    close_brackets = raw.count(']')
    
    # Check if we're inside an unterminated string
    # Find the last complete field
    last_quote_pos = raw.rfind('"')
    if last_quote_pos > 0:
        # Count quotes before this position
        quotes_before = raw[:last_quote_pos].count('"')
        # If odd number of quotes, we have an unterminated string
        if quotes_before % 2 == 1:
            # Truncate at the last complete field
            last_comma = raw.rfind(',', 0, last_quote_pos)
            if last_comma > 0:
                raw = raw[:last_comma]
    
    # Close any open brackets and braces
    while close_brackets < open_brackets:
        raw += ']'
        close_brackets += 1
    
    while close_braces < open_braces:
        raw += '}'
        close_braces += 1
    
    return raw


def _repair_json_with_llm(raw: str) -> Optional[str]:
    """Attempt to repair malformed JSON using the LLM. Returns fixed JSON string or None."""
    if not rag_pipeline:
        return None
    repair_prompt = (
        "You are a JSON formatter. Fix the following content into a valid JSON object. "
        "Return ONLY valid JSON with double quotes. No extra text.\n\n"
        f"CONTENT:\n{raw}"
    )
    try:
        result = rag_pipeline.llm.invoke(
            [HumanMessage(content=repair_prompt)],
            temperature=0,
            max_tokens=1024,
            model="llama-3.1-8b-instant"
        )
        return result.content if hasattr(result, 'content') else str(result)
    except Exception as e:
        print(f"[Analysis] JSON repair failed: {e}")
        return None


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
    confidence: Optional[float] = None  # AI confidence score 0.0-1.0
    context_before: Optional[str] = None  # 20 chars before for position recovery
    context_after: Optional[str] = None  # 20 chars after for position recovery
    original_text: Optional[str] = None  # The original text that was analyzed by AI
    reasoning: Optional[str] = None  # Educational explanation of WHY this change improves the writing


class LetterAnalysisRequest(CamelCaseModel):
    content: str
    program_slug: Optional[str] = None


class LetterAnalysisResponse(CamelCaseModel):
    suggestions: List[AISuggestion]
    word_count: int
    overall_feedback: Optional[str] = None
    analysis_metadata: Optional[Dict[str, Any]] = None


# ============= STRUCTURED OUTPUT SCHEMAS =============

class LLMSuggestion(BaseModel):
    """Schema for LLM-generated suggestions (structured output)."""
    originalText: str = Field(description="The EXACT, VERBATIM text from the user's letter that contains the error - copy it character-by-character INCLUDING any errors (do NOT fix errors in this field)")
    category: str = Field(description="Category: grammar, spelling, style, or tone")
    severity: str = Field(description="Severity: info, warning, or critical")
    title: str = Field(description="Short title describing the issue")
    description: str = Field(description="Detailed explanation of the problem")
    suggestion: str = Field(description="How to improve it")
    replacement: Optional[str] = Field(default=None, description="Exact replacement text (optional)")
    reasoning: Optional[str] = Field(default=None, description="Educational explanation of WHY this improves the writing")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")


class LLMAnalysisOutput(BaseModel):
    """Schema for complete LLM analysis output (structured output)."""
    suggestions: List[LLMSuggestion] = Field(description="List of writing improvement suggestions")
    overallFeedback: Optional[str] = Field(default=None, description="Overall assessment of the letter")


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
    
    Caches analysis results based on content hash to avoid redundant API calls.
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
    
    # Calculate content hash for caching
    content_hash = hashlib.sha256(
        f"{content}:{request.program_slug or ''}".encode()
    ).hexdigest()
    
    # Check if we have a cached analysis for this exact content
    try:
        cached = supabase.table("application_letters")\
            .select("last_analysis")\
            .eq("user_id", user_id)\
            .eq("content_hash", content_hash)\
            .limit(1)\
            .execute()
        
        if cached.data and cached.data[0].get("last_analysis"):
            print(f"[Analysis] ✓ Returning cached analysis for hash {content_hash[:8]}...")
            cached_analysis = cached.data[0]["last_analysis"]
            
            # Convert cached data to response format
            suggestions = [
                AISuggestion(**sug) for sug in cached_analysis.get("suggestions", [])
            ]
            return LetterAnalysisResponse(
                suggestions=suggestions,
                word_count=cached_analysis.get("word_count", len(content.split())),
                overall_feedback=cached_analysis.get("overall_feedback"),
                analysis_metadata={"cached": True, "content_hash": content_hash}
            )
    except Exception as e:
        print(f"[Analysis] Cache check failed: {e}")
        # Continue with fresh analysis if cache check fails
    
    # Calculate word count
    word_count = len(content.split())
    
    try:
        # Fetch program context and user profile in parallel for speed
        program_context, user_profile = await asyncio.gather(
            _get_program_context(request.program_slug),
            _get_user_profile(user_id)
        )
        
        # Construct optimized prompt for letter analysis
        system_prompt = """You are a strict TUM application letter reviewer with expertise in English grammar, spelling, and academic writing.

Your PRIMARY GOAL is to find and fix ALL objective errors:
- Spelling mistakes (typos, wrong words)
- Grammar errors (subject-verb agreement, tense, articles, prepositions)
- Capitalization errors (proper nouns, sentence starts)
- Punctuation errors (missing commas, periods, apostrophes)

Your SECONDARY GOAL is to suggest improvements to:
- Tone and formality
- Structure and clarity
- Program alignment

ANALYSIS APPROACH:
1. Read the letter word-by-word looking for ANY spelling mistakes or typos
2. Check EVERY sentence for grammar issues (articles, tenses, subject-verb agreement)
3. Verify capitalization of proper nouns (TUM, Munich, etc.)
4. Only after finding all errors, suggest stylistic improvements

For each issue provide:
- category: "critical"|"grammar"|"spelling"|"tone"|"structure"|"program-alignment"
- severity: "critical" (wrong program), "warning" (errors), "info" (improvements)
- title: Brief issue description
- description: What's wrong (under 100 chars)
- suggestion: How to fix it
- originalText: EXACT text from letter (word-for-word, complete phrase/sentence with ALL context)
- replacement: The COMPLETE, FINAL corrected version of originalText (same scope, all errors fixed)
- confidence: 0.0-1.0 score (0.9+ for objective errors, lower for subjective)
- reasoning: WHY this improves writing (1-2 sentences)

CRITICAL RULES FOR originalText AND replacement:
1. originalText MUST be the EXACT, VERBATIM text from the user's letter AS IT IS CURRENTLY WRITTEN
   - Copy it character-by-character INCLUDING ANY ERRORS
   - If the letter says "Technical University" (missing 'the'), originalText MUST be "Technical University" (NOT "the Technical University")
   - If the letter says "i am intrested" (lowercase i, spelling error), originalText MUST be "i am intrested" (NOT "I am interested")
   - DO NOT fix ANY errors in originalText - that's what replacement is for
2. originalText should contain the COMPLETE phrase or sentence that needs fixing (not just the error word)
3. replacement MUST be the COMPLETE, FINAL corrected version of originalText
4. replacement MUST have the same scope as originalText - same number of sentences/phrases
5. DO NOT make originalText just the error word - include full context (complete sentence or phrase)
6. replacement should NEVER be shorter than 40% of originalText (unless it's a 1-2 word fix)
7. Fix ALL errors in the originalText span together in one replacement - never partial fixes

EXAMPLES - CORRECT FORMAT (✓):
✓ User wrote: "I am very intrested in this programm because its a great opportunity."
✓ originalText: "I am very intrested in this programm because its a great opportunity."
✓ replacement: "I am very interested in this program because it's an excellent opportunity."
(Complete sentence, originalText has EXACT verbatim text WITH errors, all errors fixed in replacement)

✓ User wrote: "i have worked in machine learning projects."
✓ originalText: "i have worked in machine learning projects."
✓ replacement: "I have worked on machine learning projects."
(originalText has lowercase 'i' and 'in' - copied exactly as user wrote it)

✓ User wrote: "The program at Technical University of Munich is excellent."
✓ originalText: "The program at Technical University of Munich is excellent."
✓ replacement: "The program at the Technical University of Munich is excellent."
(originalText is missing 'the' - copied exactly as user wrote it, replacement adds it)

EXAMPLES - WRONG FORMAT (✗ DO NOT DO THIS):
✗ User wrote: "Technical University of Munich"
✗ originalText: "the Technical University of Munich"  ← WRONG! Added 'the' that wasn't in original
✗ replacement: "the Technical University of Munich"
(This will FAIL - originalText must match user's text exactly, including the error)

✗ User wrote: "i am intrested in this program"
✗ originalText: "I am interested in this program"  ← WRONG! Already fixed the errors
✗ replacement: "I am interested in this program"
(originalText must have lowercase 'i' and 'intrested' spelling - EXACT copy of what user wrote)

✗ originalText: "intrested"  ← WRONG! Too narrow
✗ replacement: "interested"
(Too narrow - missing context, will cause word duplication/deletion)

✗ originalText: "I am very intrested in this programm"
✗ replacement: "interested in this program"  ← WRONG! Missing words
(Replacement missing words from original - will delete "I am very")

GENERAL RULES:
1. DO NOT say "no issues found" if there are ANY spelling or grammar errors
2. Be THOROUGH - check every word for typos
3. Mark spelling/grammar errors as severity: "warning" (not "info")
4. Return 8-15 suggestions for typical letters - if you find fewer than 5, re-read more carefully
5. Each suggestion should fix a COMPLETE thought/sentence, not individual words

Return JSON with ALL errors found, prioritizing objective errors over stylistic suggestions."""

        # Build user message parts
        program_context_text = f"PROGRAM CONTEXT (for reference only, do not analyze):\n{program_context}\n\n" if program_context else ""
        
        user_message = f"""ANALYZE THIS LETTER THOROUGHLY FOR ALL ERRORS:

{program_context_text}LETTER TO REVIEW:
{content}

Target Program: {request.program_slug}

INSTRUCTIONS:
1. Read WORD-BY-WORD looking for spelling mistakes, typos, grammar errors
2. Check EVERY sentence for: missing articles (a/an/the), wrong prepositions, tense errors, subject-verb agreement
3. Verify capitalization of all proper nouns
4. Find punctuation errors
5. Then suggest tone/style improvements

DO NOT return empty suggestions if there are ANY errors.
For each error found, provide the COMPLETE corrected version fixing ALL issues in that span.

Return JSON with ALL errors found (expect 8-15 for typical letters)."""

        # Call LLM for analysis with structured output (70B model with Dev Tier)
        loop = asyncio.get_event_loop()
        
        try:
            # Use structured output for guaranteed valid JSON
            structured_llm = rag_pipeline.llm.with_structured_output(LLMAnalysisOutput)
            response = await loop.run_in_executor(
                None,
                lambda: structured_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ], temperature=0.2, max_tokens=2500, model="llama-3.3-70b-versatile")
            )
            
            # Structured output returns parsed object directly
            suggestions_data = [sug.model_dump() for sug in response.suggestions]
            overall_feedback = response.overallFeedback
            print(f"[Analysis] ✓ Structured output with 70B model: {len(suggestions_data)} suggestions")
            
        except Exception as e:
            print(f"[Analysis] Structured output failed: {e}, falling back to manual parsing...")
            # Fallback to manual parsing
            response = await loop.run_in_executor(
                None,
                lambda: rag_pipeline.llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ], temperature=0.2, max_tokens=2500, model="llama-3.3-70b-versatile")
            )
        
        
        # Parse LLM response with robust error handling
        if 'suggestions_data' not in locals():
            # Manual parsing fallback
            response_content = response.content if hasattr(response, 'content') else str(response)
            suggestions_data = []
            overall_feedback = None
            
            # Handle potential truncation first
            response_content = _handle_truncated_json(response_content)
            
            try:
                parsed = json.loads(response_content)
                suggestions_data = parsed.get("suggestions", [])
                overall_feedback = parsed.get("overallFeedback")
                print(f"[Analysis] ✓ Direct JSON parse successful")
            except json.JSONDecodeError as e:
                print(f"[Analysis] Initial JSON parse failed: {e}, attempting recovery...")
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            candidate = None
            if json_match:
                candidate = json_match.group(1)
                print(f"[Analysis] Found JSON in code block")
            else:
                # Try balanced bracket extraction
                candidate = _extract_json_candidate(response_content)
                if candidate:
                    print(f"[Analysis] Extracted balanced JSON candidate")
                else:
                    # Last resort: regex search for suggestions object
                    json_match = re.search(r'\{.*"suggestions".*\}', response_content, re.DOTALL)
                    if json_match:
                        candidate = json_match.group(0)
                        print(f"[Analysis] Found suggestions object via regex")

            if candidate:
                cleaned = _clean_json_string(candidate)
                try:
                    parsed = json.loads(cleaned)
                    suggestions_data = parsed.get("suggestions", [])
                    overall_feedback = parsed.get("overallFeedback")
                    print(f"[Analysis] ✓ Cleaned JSON parse successful")
                except json.JSONDecodeError as e2:
                    print(f"[Analysis] Cleaned JSON failed: {e2}, attempting LLM repair...")
                    repaired = _repair_json_with_llm(cleaned) or _repair_json_with_llm(response_content)
                    if repaired:
                        try:
                            repaired_clean = _clean_json_string(repaired)
                            parsed = json.loads(repaired_clean)
                            suggestions_data = parsed.get("suggestions", [])
                            overall_feedback = parsed.get("overallFeedback")
                            print(f"[Analysis] ✓ LLM repair successful")
                        except json.JSONDecodeError as e3:
                            print(f"[Analysis] ✗ LLM repair also failed: {e3}")
                            print(f"[Analysis] Raw response (first 500 chars): {response_content[:500]}")
                            # Graceful fallback: return empty suggestions
                            suggestions_data = []
                            overall_feedback = "Analysis failed due to malformed response. Please try again."
                    else:
                        print(f"[Analysis] ✗ LLM repair returned None")
                        print(f"[Analysis] Raw response (first 500 chars): {response_content[:500]}")
                        suggestions_data = []
                        overall_feedback = "Analysis failed due to malformed response. Please try again."
            else:
                # No candidate found at all
                print(f"[Analysis] ✗ Could not find any JSON candidate")
                print(f"[Analysis] Raw response (first 500 chars): {response_content[:500]}")
                suggestions_data = []
                overall_feedback = "Analysis failed due to malformed response. Please try again."
        
        # Convert to AISuggestion models
        suggestions = []
        for i, sug in enumerate(suggestions_data[:25]):  # Increased limit to 25 suggestions
            try:
                # Build highlight range by finding the original text in content
                highlight_range = None
                original_text = sug.get("originalText")
                start_pos = None
                end_pos = None
                context_before = None
                context_after = None

                if original_text and isinstance(original_text, str):
                    # 1) Exact match
                    start_pos = content.find(original_text)
                    if start_pos >= 0:
                        end_pos = start_pos + len(original_text)
                    else:
                        # 2) Case-insensitive match
                        lower_content = content.lower()
                        lower_original = original_text.lower()
                        start_pos = lower_content.find(lower_original)
                        if start_pos >= 0:
                            end_pos = start_pos + len(original_text)
                        else:
                            # 3) Whitespace-flexible regex match
                            pattern_text = re.sub(r"\s+", r"\\s+", re.escape(original_text.strip()))
                            regex = re.compile(pattern_text, re.IGNORECASE | re.DOTALL)
                            match = regex.search(content)
                            if match:
                                start_pos, end_pos = match.span()

                    if start_pos is not None and end_pos is not None:
                        # Validate replacement to prevent content deletion
                        replacement = sug.get("replacement")
                        if replacement and original_text:
                            original_words = len(original_text.strip().split())
                            replacement_words = len(replacement.strip().split())
                            
                            # Reject if replacement would delete significant content
                            if replacement_words < original_words * 0.5 and original_words >= 4:
                                print(
                                    f"[Validation] Rejected bad replacement - would delete content. "
                                    f"Original: {original_words} words, Replacement: {replacement_words} words. "
                                    f"Original: '{original_text[:50]}...', Replacement: '{replacement[:50]}...'"
                                )
                                # Downgrade to info suggestion without actionable replacement
                                highlight_range = HighlightRange(
                                    start=start_pos,
                                    end=end_pos
                                )
                                # Generate content-based ID for rejected suggestion with position
                                position_key = f"{start_pos}-{end_pos}"
                                suggestion_id_input = f"{original_text or 'unknown'}:{position_key}:{sug.get('category', 'info')}:info:{i}"
                                suggestion_id = hashlib.sha256(suggestion_id_input.encode()).hexdigest()[:12]
                                
                                suggestion = AISuggestion(
                                    id=suggestion_id,
                                    category=sug.get("category", "info"),
                                    severity="info",  # Downgrade severity
                                    title=sug.get("title", "Suggestion"),
                                    description=sug.get("description", ""),
                                    suggestion=f"{sug.get('suggestion', '')} (Note: Automatic replacement rejected to prevent content deletion)",
                                    replacement=None,  # No replacement = not actionable
                                    highlight_range=highlight_range,
                                    reasoning=sug.get("reasoning")
                                )
                                suggestions.append(suggestion)
                                continue  # Skip normal processing

                        highlight_range = HighlightRange(
                            start=start_pos,
                            end=end_pos
                        )

                        # Extract context for position recovery - increased from 20 to 40 chars
                        context_before = content[max(0, start_pos - 40):start_pos]
                        context_after = content[end_pos:min(len(content), end_pos + 40)]

                        print(f"[Analysis] ✓ Found '{original_text[:50]}...' at position {start_pos}-{end_pos}")
                    else:
                        # Keep suggestion even if we cannot find exact text
                        print(f"[Analysis] ⚠️ Could not find exact text; keeping suggestion without highlight: '{original_text[:100]}'")
                
                # Extract confidence score from structured output
                confidence = sug.get("confidence")
                if confidence is not None:
                    try:
                        confidence = float(confidence)
                        confidence = max(0.0, min(1.0, confidence))
                    except (ValueError, TypeError):
                        confidence = None
                
                # Generate content-based ID to ensure same suggestion always has same ID
                # Include position + index to handle same issue appearing multiple times
                position_key = f"{start_pos}-{end_pos}" if highlight_range else "nopos"
                suggestion_id_input = f"{original_text or 'unknown'}:{position_key}:{sug.get('category', 'info')}:{sug.get('severity', 'info')}:{i}"
                suggestion_id = hashlib.sha256(suggestion_id_input.encode()).hexdigest()[:12]
                
                suggestion = AISuggestion(
                    id=suggestion_id,
                    category=sug.get("category", "info"),
                    severity=sug.get("severity", "info"),
                    title=sug.get("title", "Suggestion"),
                    description=sug.get("description", ""),
                    suggestion=sug.get("suggestion", ""),
                    replacement=sug.get("replacement"),
                    highlight_range=highlight_range,
                    confidence=confidence,
                    context_before=context_before if highlight_range else None,
                    context_after=context_after if highlight_range else None,
                    original_text=original_text if isinstance(original_text, str) else None,
                    reasoning=sug.get("reasoning")
                )
                suggestions.append(suggestion)
            except Exception as e:
                print(f"Error parsing suggestion {i}: {e}")
                continue
        
        # Prepare response
        response_data = LetterAnalysisResponse(
            suggestions=suggestions,
            word_count=word_count,
            overall_feedback=overall_feedback,
            analysis_metadata={
                "program_slug": request.program_slug,
                "has_program_context": bool(program_context),
                "has_user_profile": bool(user_profile),
                "total_suggestions": len(suggestions),
                "cached": False,
                "content_hash": content_hash
            }
        )
        
        # Cache the analysis results in background
        try:
            # Find or create letter entry to cache analysis
            cache_data = {
                "last_analysis": {
                    "suggestions": [sug.model_dump() for sug in suggestions],
                    "word_count": word_count,
                    "overall_feedback": overall_feedback
                },
                "content_hash": content_hash
            }
            
            # Get current version and increment it
            current_letter = supabase.table("application_letters")\
                .select("analysis_version")\
                .eq("user_id", user_id)\
                .eq("content", content)\
                .limit(1)\
                .execute()
            
            if current_letter.data:
                current_version = current_letter.data[0].get("analysis_version", 0)
                cache_data["analysis_version"] = current_version + 1
            
            # Try to update existing letter with this content
            supabase.table("application_letters")\
                .update(cache_data)\
                .eq("user_id", user_id)\
                .eq("content", content)\
                .execute()
            
            print(f"[Analysis] ✓ Cached analysis for hash {content_hash[:8]}...")
        except Exception as e:
            print(f"[Analysis] Warning: Failed to cache results: {e}")
            # Don't fail the request if caching fails
        
        return response_data
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Analysis failed: {str(e)}")
