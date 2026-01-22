"""
Demo/Test Script for Evaluation Framework

This script demonstrates the evaluation framework without requiring
full RAG pipeline initialization. Uses mock responses for testing.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
CURRENT_DIR = Path(__file__).parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from evaluation.metrics import EvaluationMetrics
from evaluation.test_case_loader import TestCaseLoader


class MockChatbotInterface:
    """
    Mock chatbot interface for testing the evaluation framework.
    Returns pre-defined responses instead of querying the real chatbot.
    """
    
    def __init__(self):
        # Define mock responses for known questions
        self.mock_responses = {
            "What is the application deadline for TUM Informatics Master's program?": 
                "The application deadline for TUM Informatics Master's program is May 31 for the winter semester (starting in October). The application period runs from February 1 to May 31. For the summer semester, the deadline is November 30, with applications opening on October 1. You should apply through the TUMonline portal.",
            
            "What are the admission requirements for TUM Informatics Master's?":
                "The admission requirements for TUM Informatics Master's include: 1) A recognized undergraduate degree (e.g., Bachelor's degree), 2) Successful completion of the aptitude assessment procedure, and 3) Proof of English language proficiency. The aptitude assessment evaluates your Bachelor's grades and written documents, and may include an interview."
        }
        
        # Mock retrieved documents
        self.mock_documents = [
            {
                "content": "Application period for the winter semester: 01.02. – 31.05. Application period for the summer semester: 01.10. – 30.11. During the application period, you must apply through the TUMonline application portal and upload your application documents.",
                "metadata": {"source": "informatics-master-of-science-msc.json"}
            },
            {
                "content": "Minimum requirements to apply for a Master's program at TUM are a recognized undergraduate degree (e.g. a Bachelor's) and the successful completion of the aptitude assessment procedure. The aptitude assessment allows the TUM school to evaluate your individual talents and motivation for study.",
                "metadata": {"source": "informatics-master-of-science-msc.json"}
            }
        ]
    
    def query_chatbot(
        self,
        question: str,
        context: Optional[Dict] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Return mock response for the question."""
        return self.mock_responses.get(
            question,
            "I don't have specific information about that. Please contact TUM directly."
        )
    
    def get_retrieved_documents(self, question: str) -> List[Dict]:
        """Return mock retrieved documents."""
        return self.mock_documents


def demo_metrics():
    """Demonstrate individual metrics."""
    print("="*70)
    print("DEMO: Individual Metrics")
    print("="*70)
    
    metrics = EvaluationMetrics()
    
    # Example 1: Good answer
    print("\n--- Example 1: Good Answer ---")
    question = "What is the application deadline for TUM Informatics?"
    answer = "The deadline is May 31 for winter semester and November 30 for summer semester."
    keywords = ["May 31", "winter semester", "November 30"]
    ground_truth = {"deadline_winter": "May 31", "deadline_summer": "November 30"}
    
    factual = metrics.factual_accuracy(answer, ground_truth, keywords)
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print(f"Factual Accuracy: {factual['score']:.3f}")
    print(f"  Keywords found: {factual['details']['keywords_found']}")
    
    relevance = metrics.relevance(answer, question)
    print(f"Relevance: {relevance['score']:.3f}")
    print(f"  Is deflection: {relevance['details']['is_deflection']}")
    
    # Example 2: Bad answer (deflection)
    print("\n--- Example 2: Bad Answer (Deflection) ---")
    bad_answer = "Please check the TUM website for more information."
    
    factual = metrics.factual_accuracy(bad_answer, ground_truth, keywords)
    print(f"Answer: {bad_answer}")
    print(f"Factual Accuracy: {factual['score']:.3f}")
    print(f"  Keywords found: {factual['details']['keywords_found']}")
    
    relevance = metrics.relevance(bad_answer, question)
    print(f"Relevance: {relevance['score']:.3f}")
    print(f"  Is deflection: {relevance['details']['is_deflection']}")


def demo_test_case_evaluation():
    """Demonstrate evaluating a single test case."""
    print("\n" + "="*70)
    print("DEMO: Test Case Evaluation")
    print("="*70)
    
    # Load test dataset
    loader = TestCaseLoader()
    dataset = loader.load_dataset('tum_informatics_deadlines_factual')
    test_case = dataset['test_cases'][0]
    
    print(f"\nTest ID: {test_case['test_id']}")
    print(f"Question: {test_case['question']}")
    
    # Mock chatbot
    chatbot = MockChatbotInterface()
    
    # Get answer
    answer = chatbot.query_chatbot(test_case['question'])
    print(f"\nChatbot Answer:\n{answer}")
    
    # Get documents
    docs = chatbot.get_retrieved_documents(test_case['question'])
    print(f"\nRetrieved {len(docs)} documents")
    
    # Calculate metrics
    metrics = EvaluationMetrics()
    expected = test_case['expected_output']
    
    factual = metrics.factual_accuracy(
        answer,
        expected['ground_truth'],
        expected['must_include_keywords']
    )
    
    groundedness = metrics.groundedness(answer, docs)
    
    relevance = metrics.relevance(answer, test_case['question'])
    
    overall = metrics.calculate_weighted_score(
        factual, groundedness, relevance,
        weights={'factual_accuracy': 0.5, 'groundedness': 0.3, 'relevance': 0.2}
    )
    
    # Print results
    print("\n--- Evaluation Results ---")
    print(f"Factual Accuracy: {factual['score']:.3f}")
    print(f"  Keywords found: {factual['details']['keywords_found']}")
    print(f"  Keywords missing: {factual['details']['keywords_missing']}")
    
    print(f"\nGroundedness: {groundedness['score']:.3f}")
    print(f"  Grounded: {groundedness['details']['grounded']}")
    print(f"  Grounded sentences: {groundedness['details']['grounded_sentences']}/{groundedness['details']['total_sentences']}")
    
    print(f"\nRelevance: {relevance['score']:.3f}")
    print(f"  Is deflection: {relevance['details']['is_deflection']}")
    
    print(f"\nOverall Score: {overall:.3f}")
    
    # Check thresholds
    eval_config = test_case.get('evaluation_metrics', {})
    print("\n--- Threshold Checks ---")
    
    for metric_name, metric_result in [
        ('factual_accuracy', factual),
        ('groundedness', groundedness),
        ('relevance', relevance)
    ]:
        if metric_name in eval_config:
            threshold = eval_config[metric_name].get('threshold', 0.9)
            passes = metric_result['score'] >= threshold
            status = "✓ PASS" if passes else "✗ FAIL"
            print(f"{metric_name}: {metric_result['score']:.3f} >= {threshold} {status}")


def demo_full_dataset():
    """Demonstrate evaluating a full dataset with mock chatbot."""
    print("\n" + "="*70)
    print("DEMO: Full Dataset Evaluation (Mock)")
    print("="*70)
    
    loader = TestCaseLoader()
    dataset = loader.load_dataset('tum_informatics_deadlines_factual')
    
    print(f"\nDataset: {dataset['dataset_name']}")
    print(f"Version: {dataset['version']}")
    print(f"Test cases: {len(dataset['test_cases'])}")
    
    chatbot = MockChatbotInterface()
    metrics_calc = EvaluationMetrics()
    
    results = []
    
    for test_case in dataset['test_cases']:
        test_id = test_case['test_id']
        question = test_case['question']
        expected = test_case['expected_output']
        
        print(f"\n--- Test: {test_id} ---")
        print(f"Question: {question}")
        
        # Get answer
        answer = chatbot.query_chatbot(question)
        print(f"Answer: {answer[:100]}...")
        
        # Calculate metrics
        factual = metrics_calc.factual_accuracy(
            answer, expected['ground_truth'], expected['must_include_keywords']
        )
        groundedness = metrics_calc.groundedness(
            answer, chatbot.get_retrieved_documents(question)
        )
        relevance = metrics_calc.relevance(answer, question)
        overall = metrics_calc.calculate_weighted_score(
            factual, groundedness, relevance
        )
        
        print(f"Scores: Factual={factual['score']:.2f}, Ground={groundedness['score']:.2f}, Rel={relevance['score']:.2f}, Overall={overall:.2f}")
        
        results.append({
            'test_id': test_id,
            'overall_score': overall,
            'factual': factual['score'],
            'groundedness': groundedness['score'],
            'relevance': relevance['score']
        })
    
    # Summary
    avg_overall = sum(r['overall_score'] for r in results) / len(results)
    avg_factual = sum(r['factual'] for r in results) / len(results)
    avg_groundedness = sum(r['groundedness'] for r in results) / len(results)
    avg_relevance = sum(r['relevance'] for r in results) / len(results)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total tests: {len(results)}")
    print(f"Average Overall Score: {avg_overall:.3f}")
    print(f"Average Factual Accuracy: {avg_factual:.3f}")
    print(f"Average Groundedness: {avg_groundedness:.3f}")
    print(f"Average Relevance: {avg_relevance:.3f}")


def main():
    """Run all demos."""
    print("\n" + "#"*70)
    print("# EVALUATION FRAMEWORK DEMO")
    print("#"*70)
    
    try:
        demo_metrics()
        demo_test_case_evaluation()
        demo_full_dataset()
        
        print("\n" + "="*70)
        print("✓ All demos completed successfully!")
        print("="*70)
        print("\nNext steps:")
        print("1. Review the evaluation metrics and adjust thresholds if needed")
        print("2. Create additional test case datasets for your use cases")
        print("3. Run evaluations with the real chatbot using:")
        print("   python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
