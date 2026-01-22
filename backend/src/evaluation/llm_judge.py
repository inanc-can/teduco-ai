"""
LLM-as-a-Judge Evaluation Metrics

Uses an LLM to evaluate RAG responses for:
- Factual accuracy
- Groundedness
- Relevance
- Completeness
"""

import os
from typing import Dict, List, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import json

load_dotenv()


class LLMJudge:
    """
    Use an LLM to evaluate chatbot responses.
    More flexible and semantic than keyword matching.
    """
    
    def __init__(self, model: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
        """
        Initialize the LLM judge.
        
        Args:
            model: Groq model to use for evaluation (default: llama-3.3-70b-versatile)
            temperature: Temperature for LLM (0.0 for deterministic)
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.llm = ChatGroq(
            model=model,
            temperature=temperature,
            groq_api_key=api_key
        )
    
    def evaluate_factual_accuracy(
        self,
        question: str,
        answer: str,
        ground_truth: Dict[str, Any],
        must_include_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate factual accuracy using LLM.
        
        Args:
            question: The original question
            answer: The chatbot's answer
            ground_truth: Expected facts
            must_include_keywords: Required keywords/facts
        
        Returns:
            Dictionary with score (0-1) and explanation
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator assessing the factual accuracy of chatbot answers.
            
Your task:
1. Compare the chatbot's answer to the ground truth facts
2. Check if all required information is present
3. Identify any incorrect or hallucinated information
4. Provide a score from 0.0 to 1.0 where:
   - 1.0 = Perfect accuracy, all facts correct and complete
   - 0.7-0.9 = Mostly accurate, minor details missing
   - 0.4-0.6 = Partially accurate, some important facts missing
   - 0.0-0.3 = Mostly inaccurate or missing critical information

Respond ONLY with valid JSON in this format:
{{
    "score": 0.85,
    "explanation": "Brief explanation of the score",
    "missing_facts": ["fact1", "fact2"],
    "incorrect_facts": ["wrong1"],
    "hallucinations": []
}}"""),
            ("user", """Question: {question}

Chatbot's Answer: {answer}

Ground Truth Facts: {ground_truth}

Required Keywords/Facts: {keywords}

Evaluate the answer's factual accuracy:""")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "question": question,
                "answer": answer,
                "ground_truth": json.dumps(ground_truth, indent=2),
                "keywords": ", ".join(must_include_keywords)
            })
            
            # Parse JSON from response
            result = json.loads(response.content)
            return result
            
        except Exception as e:
            print(f"Error in LLM factual accuracy evaluation: {e}")
            return {
                "score": 0.0,
                "explanation": f"Evaluation failed: {str(e)}",
                "missing_facts": [],
                "incorrect_facts": [],
                "hallucinations": []
            }
    
    def evaluate_groundedness(
        self,
        answer: str,
        retrieved_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate if answer is grounded in retrieved documents.
        
        Args:
            answer: The chatbot's answer
            retrieved_documents: Documents retrieved by RAG
        
        Returns:
            Dictionary with score and explanation
        """
        # Extract text from documents
        doc_texts = []
        for doc in retrieved_documents[:5]:  # Use top 5 docs
            if 'content' in doc:
                doc_texts.append(doc['content'])
            elif 'page_content' in doc:
                doc_texts.append(doc['page_content'])
        
        docs_text = "\n\n---\n\n".join(doc_texts)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator assessing whether chatbot answers are grounded in source documents.

Your task:
1. Check if every claim in the answer can be verified in the provided documents
2. Identify any claims not supported by the documents (hallucinations)
3. Provide a score from 0.0 to 1.0 where:
   - 1.0 = Every claim is directly supported by documents
   - 0.7-0.9 = Most claims supported, minor unsupported details
   - 0.4-0.6 = Some claims supported, but significant unsupported content
   - 0.0-0.3 = Most claims not supported by documents

Respond ONLY with valid JSON in this format:
{{
    "score": 0.9,
    "explanation": "Brief explanation",
    "supported_claims": ["claim1", "claim2"],
    "unsupported_claims": ["claim3"],
    "hallucinations": []
}}"""),
            ("user", """Answer to Evaluate: {answer}

Retrieved Documents:
{documents}

Evaluate groundedness:""")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "answer": answer,
                "documents": docs_text[:4000]  # Limit context size
            })
            
            result = json.loads(response.content)
            return result
            
        except Exception as e:
            print(f"Error in LLM groundedness evaluation: {e}")
            return {
                "score": 0.0,
                "explanation": f"Evaluation failed: {str(e)}",
                "supported_claims": [],
                "unsupported_claims": [],
                "hallucinations": []
            }
    
    def evaluate_relevance(
        self,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Evaluate if answer is relevant to the question.
        
        Args:
            question: The original question
            answer: The chatbot's answer
        
        Returns:
            Dictionary with score and explanation
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator assessing answer relevance.

Your task:
1. Determine if the answer addresses the question asked
2. Check for deflections (e.g., "check the website")
3. Assess completeness of the answer
4. Provide a score from 0.0 to 1.0 where:
   - 1.0 = Directly answers question, complete and helpful
   - 0.7-0.9 = Answers question but missing some details
   - 0.4-0.6 = Partially relevant, some deflection
   - 0.0-0.3 = Doesn't answer question or complete deflection

Respond ONLY with valid JSON in this format:
{{
    "score": 0.85,
    "explanation": "Brief explanation",
    "is_deflection": false,
    "addresses_question": true,
    "completeness": "complete|partial|incomplete"
}}"""),
            ("user", """Question: {question}

Answer: {answer}

Evaluate relevance:""")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "question": question,
                "answer": answer
            })
            
            result = json.loads(response.content)
            return result
            
        except Exception as e:
            print(f"Error in LLM relevance evaluation: {e}")
            return {
                "score": 0.0,
                "explanation": f"Evaluation failed: {str(e)}",
                "is_deflection": True,
                "addresses_question": False,
                "completeness": "incomplete"
            }
    
    def evaluate_all(
        self,
        question: str,
        answer: str,
        ground_truth: Dict[str, Any],
        must_include_keywords: List[str],
        retrieved_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run all evaluations and combine results.
        
        Returns:
            Combined evaluation results
        """
        factual = self.evaluate_factual_accuracy(
            question, answer, ground_truth, must_include_keywords
        )
        
        groundedness = self.evaluate_groundedness(
            answer, retrieved_documents
        )
        
        relevance = self.evaluate_relevance(
            question, answer
        )
        
        # Weighted average
        overall_score = (
            factual['score'] * 0.5 +
            groundedness['score'] * 0.3 +
            relevance['score'] * 0.2
        )
        
        return {
            'overall_score': overall_score,
            'factual_accuracy': factual,
            'groundedness': groundedness,
            'relevance': relevance
        }
