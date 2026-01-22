"""
Evaluation Metrics for LLM Chatbot

This module implements various evaluation metrics:
- Factual Accuracy
- Groundedness (answer based on retrieved documents)
- Relevance (answer addresses the question)
"""

import re
from typing import List, Dict, Optional, Any
from difflib import SequenceMatcher


class EvaluationMetrics:
    """
    Calculate evaluation metrics for chatbot responses.
    """
    
    @staticmethod
    def factual_accuracy(
        answer: str,
        ground_truth: Dict[str, Any],
        must_include_keywords: List[str],
        scoring_rules: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate factual accuracy of the answer.
        
        Args:
            answer: The chatbot's answer
            ground_truth: Dictionary containing expected factual information
            must_include_keywords: List of keywords that must appear in the answer
            scoring_rules: Optional dictionary with scoring weights for each aspect
        
        Returns:
            Dictionary with score and details
        """
        score = 0.0
        details = {}
        answer_lower = answer.lower()
        
        # Check for must-include keywords
        keyword_score = 0.0
        keywords_found = []
        keywords_missing = []
        
        for keyword in must_include_keywords:
            if keyword.lower() in answer_lower:
                keywords_found.append(keyword)
                keyword_score += 1.0
            else:
                keywords_missing.append(keyword)
        
        if must_include_keywords:
            keyword_score = keyword_score / len(must_include_keywords)
        
        details['keywords_found'] = keywords_found
        details['keywords_missing'] = keywords_missing
        details['keyword_score'] = keyword_score
        
        # Apply scoring rules if provided
        if scoring_rules:
            rule_scores = {}
            for rule_name, weight in scoring_rules.items():
                # Check if the rule is satisfied (simple keyword check)
                rule_satisfied = False
                if rule_name in ground_truth:
                    expected_value = str(ground_truth[rule_name]).lower()
                    if expected_value in answer_lower:
                        rule_satisfied = True
                        rule_scores[rule_name] = weight
                    else:
                        rule_scores[rule_name] = 0.0
                else:
                    # Generic rule check
                    rule_scores[rule_name] = weight if keyword_score > 0.5 else 0.0
            
            score = sum(rule_scores.values())
            details['rule_scores'] = rule_scores
        else:
            score = keyword_score
        
        return {
            'score': score,
            'details': details
        }
    
    @staticmethod
    def groundedness(
        answer: str,
        retrieved_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate if the answer is grounded in the retrieved documents.
        
        Args:
            answer: The chatbot's answer
            retrieved_documents: List of retrieved document dictionaries
        
        Returns:
            Dictionary with score and details
        """
        if not retrieved_documents:
            return {
                'score': 0.0,
                'details': {
                    'grounded': False,
                    'reason': 'No documents retrieved'
                }
            }
        
        # Extract text from documents
        doc_texts = []
        for doc in retrieved_documents:
            if 'content' in doc:
                doc_texts.append(doc['content'].lower())
            elif 'page_content' in doc:
                doc_texts.append(doc['page_content'].lower())
        
        if not doc_texts:
            return {
                'score': 0.0,
                'details': {
                    'grounded': False,
                    'reason': 'No content in retrieved documents'
                }
            }
        
        # Combine all document text
        combined_docs = ' '.join(doc_texts)
        answer_lower = answer.lower()
        
        # Split answer into sentences
        sentences = re.split(r'[.!?]+', answer_lower)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {
                'score': 0.0,
                'details': {
                    'grounded': False,
                    'reason': 'Empty answer'
                }
            }
        
        # Check how many sentences can be found (or have high overlap) in documents
        grounded_sentences = 0
        sentence_details = []
        
        for sentence in sentences:
            # Check for high overlap with any part of the documents
            best_match_ratio = 0.0
            
            # Split documents into similar-length chunks for comparison
            words = sentence.split()
            sentence_length = len(words)
            
            if sentence_length > 0:
                # Look for sentence in documents
                if sentence in combined_docs:
                    best_match_ratio = 1.0
                else:
                    # Check for partial matches using sequence matching
                    for doc_text in doc_texts:
                        # Find best substring match
                        matcher = SequenceMatcher(None, sentence, doc_text)
                        match_ratio = matcher.ratio()
                        best_match_ratio = max(best_match_ratio, match_ratio)
            
            # Consider grounded if match ratio > 0.5
            is_grounded = best_match_ratio > 0.5
            if is_grounded:
                grounded_sentences += 1
            
            sentence_details.append({
                'sentence': sentence,
                'match_ratio': best_match_ratio,
                'grounded': is_grounded
            })
        
        # Calculate overall groundedness score
        score = grounded_sentences / len(sentences) if sentences else 0.0
        
        return {
            'score': score,
            'details': {
                'grounded': score > 0.8,
                'grounded_sentences': grounded_sentences,
                'total_sentences': len(sentences),
                'sentence_details': sentence_details
            }
        }
    
    @staticmethod
    def relevance(
        answer: str,
        question: str,
        expected_topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate if the answer is relevant to the question.
        
        Args:
            answer: The chatbot's answer
            question: The user's question
            expected_topics: Optional list of topics that should be addressed
        
        Returns:
            Dictionary with score and details
        """
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # Extract key terms from the question (simple approach)
        # Remove common words
        stop_words = {'what', 'is', 'the', 'a', 'an', 'are', 'when', 'where', 
                     'how', 'why', 'which', 'who', 'for', 'of', 'in', 'on', 
                     'at', 'to', 'from', 'by', 'with', 'about', 'as', 'or', 'and'}
        
        question_words = question_lower.split()
        key_terms = [w for w in question_words if w not in stop_words and len(w) > 2]
        
        # Check how many key terms appear in the answer
        terms_found = []
        terms_missing = []
        
        for term in key_terms:
            if term in answer_lower:
                terms_found.append(term)
            else:
                terms_missing.append(term)
        
        # Calculate term overlap score
        term_score = len(terms_found) / len(key_terms) if key_terms else 0.5
        
        # Check for expected topics if provided
        topic_score = 1.0
        topics_found = []
        topics_missing = []
        
        if expected_topics:
            for topic in expected_topics:
                if topic.lower() in answer_lower:
                    topics_found.append(topic)
                else:
                    topics_missing.append(topic)
            
            topic_score = len(topics_found) / len(expected_topics) if expected_topics else 1.0
        
        # Check if answer is a deflection (e.g., "I don't know", "contact us")
        deflection_phrases = [
            "i don't have",
            "i don't know",
            "contact",
            "check the website",
            "visit the website",
            "not available",
            "no information"
        ]
        
        is_deflection = any(phrase in answer_lower for phrase in deflection_phrases)
        
        # Calculate overall relevance score
        # If it's a deflection, score is lower
        if is_deflection:
            score = min(0.3, term_score * 0.5)
        else:
            score = (term_score * 0.6 + topic_score * 0.4)
        
        return {
            'score': score,
            'details': {
                'relevant': score > 0.7,
                'term_overlap': term_score,
                'topic_coverage': topic_score,
                'terms_found': terms_found,
                'terms_missing': terms_missing,
                'topics_found': topics_found,
                'topics_missing': topics_missing,
                'is_deflection': is_deflection
            }
        }
    
    @staticmethod
    def calculate_weighted_score(
        factual_result: Dict[str, Any],
        groundedness_result: Dict[str, Any],
        relevance_result: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate overall weighted score from individual metrics.
        
        Args:
            factual_result: Result from factual_accuracy()
            groundedness_result: Result from groundedness()
            relevance_result: Result from relevance()
            weights: Optional dictionary with weights for each metric
        
        Returns:
            Overall weighted score (0-1)
        """
        if weights is None:
            weights = {
                'factual_accuracy': 0.5,
                'groundedness': 0.3,
                'relevance': 0.2
            }
        
        overall_score = (
            factual_result['score'] * weights.get('factual_accuracy', 0.5) +
            groundedness_result['score'] * weights.get('groundedness', 0.3) +
            relevance_result['score'] * weights.get('relevance', 0.2)
        )
        
        return overall_score
