"""
Chatbot Interface for Evaluation Framework

This module provides a clean interface to query the Teduco-AI chatbot
for evaluation purposes.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List

# Add parent directories to path
CURRENT_DIR = Path(__file__).parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from rag.chatbot.pipeline import RAGChatbotPipeline


class ChatbotInterface:
    """
    Interface to query the chatbot for evaluation purposes.
    
    This class wraps the RAG pipeline and provides a consistent interface
    for the evaluation framework.
    """
    
    def __init__(
        self,
        rag_pipeline: Optional[RAGChatbotPipeline] = None,
        data_dir: str = "/home/runner/work/teduco-ai/teduco-ai/backend/rag_data"
    ):
        """
        Initialize the chatbot interface.
        
        Args:
            rag_pipeline: Existing RAG pipeline instance (optional)
            data_dir: Directory for RAG data (used if rag_pipeline not provided)
        """
        if rag_pipeline is None:
            from rag.chatbot.pipeline import initialize_rag_pipeline
            self.rag_pipeline = initialize_rag_pipeline(
                data_dir=data_dir,
                use_cache=True
            )
        else:
            self.rag_pipeline = rag_pipeline
    
    def query_chatbot(
        self,
        question: str,
        context: Optional[Dict] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Query the chatbot and return the answer.
        
        Args:
            question: User's question
            context: Optional context dictionary (for future use)
            chat_history: Optional chat history in format:
                         [{"role": "user", "content": "..."}, ...]
        
        Returns:
            Answer string from the chatbot
        """
        try:
            # Use the agent if available, otherwise use answer_question
            if hasattr(self.rag_pipeline, 'agent') and self.rag_pipeline.agent:
                # Agent can handle user_id, but for evaluation we don't have one
                answer = self.rag_pipeline.agent.run(
                    question,
                    user_id=None,
                    chat_history=chat_history or []
                )
            else:
                answer = self.rag_pipeline.answer_question(
                    question,
                    chat_history=chat_history
                )
            return answer
        except Exception as e:
            return f"Error querying chatbot: {str(e)}"
    
    def get_retrieved_documents(self, question: str) -> List[Dict]:
        """
        Get the documents retrieved for a question (for groundedness testing).
        
        Args:
            question: User's question
        
        Returns:
            List of retrieved document dictionaries
        """
        try:
            # Use the retriever directly
            query_embedding = self.rag_pipeline.retriever_pipeline.embeddings.embed_query(question)
            
            # Import retrieve_chunks
            from rag.chatbot.db_ops import retrieve_chunks
            
            results = retrieve_chunks(
                query=question,
                query_embedding=query_embedding,
                top_k=self.rag_pipeline.retriever_pipeline.k,
                semantic_weight=self.rag_pipeline.semantic_weight,
                keyword_weight=self.rag_pipeline.keyword_weight
            )
            
            return results
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
