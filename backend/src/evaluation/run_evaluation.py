#!/usr/bin/env python3
"""
Evaluation Runner Script

CLI tool to run LLM evaluations on the Teduco-AI chatbot.

Usage:
    python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual
    python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual --no-save
    python -m evaluation.run_evaluation --list-datasets
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
CURRENT_DIR = Path(__file__).parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))


def main():
    """Main entry point for the evaluation runner."""
    parser = argparse.ArgumentParser(
        description='Run LLM evaluation on Teduco-AI chatbot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run evaluation on a specific dataset
  python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual
  
  # List available datasets
  python -m evaluation.run_evaluation --list-datasets
  
  # Run evaluation without saving results
  python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual --no-save
"""
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        help='Name of the dataset to evaluate (without .json extension)'
    )
    
    parser.add_argument(
        '--list-datasets',
        action='store_true',
        help='List all available datasets'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save evaluation results to file'
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='/home/runner/work/teduco-ai/teduco-ai/backend/rag_data',
        help='Directory containing RAG data (default: /home/runner/work/teduco-ai/teduco-ai/backend/rag_data)'
    )
    
    args = parser.parse_args()
    
    # Handle --list-datasets
    if args.list_datasets:
        from evaluation.test_case_loader import TestCaseLoader
        loader = TestCaseLoader()
        datasets = loader.list_datasets()
        
        if datasets:
            print("\nAvailable datasets:")
            for dataset in datasets:
                print(f"  - {dataset}")
        else:
            print("\nNo datasets found in the datasets directory.")
        
        return 0
    
    # Require --dataset if not listing
    if not args.dataset:
        parser.print_help()
        print("\nError: --dataset is required (or use --list-datasets)")
        return 1
    
    # Initialize evaluator
    print("\nInitializing evaluator...")
    print(f"Using RAG data directory: {args.data_dir}")
    
    try:
        from evaluation.evaluator import Evaluator
        evaluator = Evaluator()
        
        # Run evaluation
        save_results = not args.no_save
        report = evaluator.evaluate_dataset(
            dataset_name=args.dataset,
            save_results=save_results
        )
        
        # Print final summary
        summary = report['summary']
        print(f"\n{'='*70}")
        print("FINAL RESULTS")
        print(f"{'='*70}")
        print(f"Pass Rate: {summary['pass_rate']:.1%} ({summary['passed']}/{summary['total_tests']})")
        print(f"Overall Score: {summary['average_scores']['overall']:.3f}")
        print(f"{'='*70}\n")
        
        # Return exit code based on pass rate
        if summary['pass_rate'] >= 0.8:  # 80% pass rate threshold
            return 0
        else:
            return 1
    
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nUse --list-datasets to see available datasets.")
        return 1
    except Exception as e:
        print(f"\nError during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
