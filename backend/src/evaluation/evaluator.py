"""
Main Evaluator for LLM Chatbot

This module orchestrates the evaluation process, running test cases and calculating metrics.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from evaluation.chatbot_interface import ChatbotInterface
from evaluation.metrics import EvaluationMetrics
from evaluation.llm_judge import LLMJudge
from evaluation.test_case_loader import TestCaseLoader


class Evaluator:
    """
    Main evaluator class that orchestrates the evaluation process.
    """
    
    def __init__(
        self,
        chatbot_interface: Optional[ChatbotInterface] = None,
        results_dir: str = None,
        judge_type: str = "llm"
    ):
        """
        Initialize the evaluator.
        
        Args:
            chatbot_interface: Interface to the chatbot
            results_dir: Directory to save evaluation results
            judge_type: Evaluation method - 'llm' or 'keyword' (default: 'llm')
        """
        self.chatbot = chatbot_interface or ChatbotInterface()
        self.judge_type = judge_type
        
        if judge_type == "llm":
            self.llm_judge = LLMJudge()
            self.metrics = None
        else:
            self.metrics = EvaluationMetrics()
            self.llm_judge = None
        
        self.loader = TestCaseLoader()
        
        if results_dir is None:
            self.results_dir = Path(__file__).parent / "results"
        else:
            self.results_dir = Path(results_dir)
        
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def evaluate_test_case(
        self,
        test_case: Dict[str, Any],
        include_retrieved_docs: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate a single test case.
        
        Args:
            test_case: Test case dictionary
            include_retrieved_docs: Whether to retrieve and evaluate groundedness
        
        Returns:
            Dictionary with evaluation results
        """
        test_id = test_case.get('test_id', 'unknown')
        question = test_case['question']
        expected_output = test_case['expected_output']
        context = test_case.get('context', {})
        eval_metrics_config = test_case.get('evaluation_metrics', {})
        
        print(f"\n{'='*70}")
        print(f"Evaluating Test Case: {test_id}")
        print(f"Question: {question}")
        print(f"{'='*70}")
        
        # Get chat history from context if available
        chat_history = context.get('conversation_history', [])
        
        # Query the chatbot
        start_time = datetime.now()
        answer = self.chatbot.query_chatbot(
            question=question,
            context=context,
            chat_history=chat_history
        )
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        print(f"\nChatbot Answer:\n{answer}")
        print(f"\nResponse Time: {response_time:.2f}s")
        
        # Get retrieved documents for groundedness check
        retrieved_docs = []
        if include_retrieved_docs:
            retrieved_docs = self.chatbot.get_retrieved_documents(question)
            print(f"\nRetrieved Documents: {len(retrieved_docs)}")
        
        # Calculate metrics based on judge type
        if self.judge_type == "llm":
            # Use LLM judge
            ground_truth = expected_output.get('ground_truth', {})
            must_include_keywords = expected_output.get('must_include_keywords', [])
            
            eval_result = self.llm_judge.evaluate_all(
                question=question,
                answer=answer,
                ground_truth=ground_truth,
                must_include_keywords=must_include_keywords,
                retrieved_documents=retrieved_docs
            )
            
            # Extract individual metrics
            factual_result = {
                'score': eval_result['factual_accuracy']['score'],
                'details': eval_result['factual_accuracy']
            }
            groundedness_result = {
                'score': eval_result['groundedness']['score'],
                'details': eval_result['groundedness']
            }
            relevance_result = {
                'score': eval_result['relevance']['score'],
                'details': eval_result['relevance']
            }
            overall_score = eval_result['overall_score']
            
        else:
            # Use keyword-based metrics
            # 1. Factual Accuracy
            ground_truth = expected_output.get('ground_truth', {})
            must_include_keywords = expected_output.get('must_include_keywords', [])
            scoring_rules = eval_metrics_config.get('factual_accuracy', {}).get('scoring_rules')
            
            factual_result = self.metrics.factual_accuracy(
                answer=answer,
                ground_truth=ground_truth,
                must_include_keywords=must_include_keywords,
                scoring_rules=scoring_rules
            )
            
            # 2. Groundedness
            groundedness_result = self.metrics.groundedness(
                answer=answer,
                retrieved_documents=retrieved_docs
            )
            
            # 3. Relevance
            expected_topics = expected_output.get('must_include_details', [])
            relevance_result = self.metrics.relevance(
                answer=answer,
                question=question,
                expected_topics=expected_topics
            )
            
            # Calculate weighted score
            weights = {}
            for metric_name in ['factual_accuracy', 'groundedness', 'relevance']:
                if metric_name in eval_metrics_config:
                    weights[metric_name] = eval_metrics_config[metric_name].get('weight', 0.33)
            
            overall_score = self.metrics.calculate_weighted_score(
                factual_result=factual_result,
                groundedness_result=groundedness_result,
                relevance_result=relevance_result,
                weights=weights if weights else None
            )
        
        # Check if test passes
        passes = True
        threshold_checks = {}
        
        for metric_name, metric_result in [
            ('factual_accuracy', factual_result),
            ('groundedness', groundedness_result),
            ('relevance', relevance_result)
        ]:
            if metric_name in eval_metrics_config:
                threshold = eval_metrics_config[metric_name].get('threshold', 0.9)
                passes_threshold = metric_result['score'] >= threshold
                threshold_checks[metric_name] = {
                    'score': metric_result['score'],
                    'threshold': threshold,
                    'passes': passes_threshold
                }
                if not passes_threshold:
                    passes = False
        
        # Print results
        print(f"\n--- Evaluation Results ({self.judge_type.upper()}) ---")
        print(f"Factual Accuracy: {factual_result['score']:.3f}")
        
        if self.judge_type == "llm":
            print(f"  Explanation: {factual_result['details'].get('explanation', 'N/A')}")
            if factual_result['details'].get('missing_facts'):
                print(f"  Missing Facts: {factual_result['details']['missing_facts']}")
        else:
            print(f"  Keywords Found: {factual_result['details']['keywords_found']}")
            print(f"  Keywords Missing: {factual_result['details']['keywords_missing']}")
        
        print(f"\nGroundedness: {groundedness_result['score']:.3f}")
        
        if self.judge_type == "llm":
            print(f"  Explanation: {groundedness_result['details'].get('explanation', 'N/A')}")
        else:
            print(f"  Grounded: {groundedness_result['details']['grounded']}")
        
        print(f"\nRelevance: {relevance_result['score']:.3f}")
        
        if self.judge_type == "llm":
            print(f"  Explanation: {relevance_result['details'].get('explanation', 'N/A')}")
        else:
            print(f"  Is Deflection: {relevance_result['details']['is_deflection']}")
        
        print(f"\nOverall Score: {overall_score:.3f}")
        print(f"Test Passes: {passes}")
        
        # Compile result
        result = {
            'test_id': test_id,
            'question': question,
            'answer': answer,
            'response_time_seconds': response_time,
            'metrics': {
                'factual_accuracy': factual_result,
                'groundedness': groundedness_result,
                'relevance': relevance_result,
                'overall_score': overall_score
            },
            'threshold_checks': threshold_checks,
            'passes': passes,
            'timestamp': datetime.now().isoformat(),
            'metadata': test_case.get('metadata', {})
        }
        
        return result
    
    def evaluate_dataset(
        self,
        dataset_name: str,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate all test cases in a dataset.
        
        Args:
            dataset_name: Name of the dataset to evaluate
            save_results: Whether to save results to a file
        
        Returns:
            Dictionary with aggregated results
        """
        print(f"\n{'='*70}")
        print(f"Evaluating Dataset: {dataset_name}")
        print(f"{'='*70}")
        
        # Load dataset
        dataset = self.loader.load_dataset(dataset_name)
        test_cases = self.loader.get_test_cases(dataset)
        
        print(f"Loaded {len(test_cases)} test cases")
        
        # Evaluate each test case
        results = []
        for test_case in test_cases:
            result = self.evaluate_test_case(test_case)
            results.append(result)
        
        # Calculate aggregate statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['passes'])
        failed_tests = total_tests - passed_tests
        
        avg_overall_score = sum(r['metrics']['overall_score'] for r in results) / total_tests if total_tests > 0 else 0
        avg_factual = sum(r['metrics']['factual_accuracy']['score'] for r in results) / total_tests if total_tests > 0 else 0
        avg_groundedness = sum(r['metrics']['groundedness']['score'] for r in results) / total_tests if total_tests > 0 else 0
        avg_relevance = sum(r['metrics']['relevance']['score'] for r in results) / total_tests if total_tests > 0 else 0
        avg_response_time = sum(r['response_time_seconds'] for r in results) / total_tests if total_tests > 0 else 0
        
        # Compile final report
        report = {
            'dataset_name': dataset_name,
            'dataset_version': dataset.get('version', 'unknown'),
            'evaluation_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'average_scores': {
                    'overall': avg_overall_score,
                    'factual_accuracy': avg_factual,
                    'groundedness': avg_groundedness,
                    'relevance': avg_relevance
                },
                'average_response_time_seconds': avg_response_time
            },
            'test_results': results
        }
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"Evaluation Summary")
        print(f"{'='*70}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Pass Rate: {report['summary']['pass_rate']:.1%}")
        print(f"\nAverage Scores:")
        print(f"  Overall: {avg_overall_score:.3f}")
        print(f"  Factual Accuracy: {avg_factual:.3f}")
        print(f"  Groundedness: {avg_groundedness:.3f}")
        print(f"  Relevance: {avg_relevance:.3f}")
        print(f"\nAverage Response Time: {avg_response_time:.2f}s")
        print(f"{'='*70}")
        
        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_filename = f"{dataset_name}_results_{timestamp}.json"
            results_path = self.results_dir / results_filename
            
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\nResults saved to: {results_path}")
        
        return report
