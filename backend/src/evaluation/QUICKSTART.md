# Quick Start Guide: LLM Evaluation Framework

This guide will help you get started with the evaluation framework in 5 minutes.

## Prerequisites

1. Python 3.8 or higher
2. All dependencies installed (if running with real chatbot)
3. GROQ_API_KEY set in environment (if running with real chatbot)

## Step 1: Verify Installation

```bash
cd /home/runner/work/teduco-ai/teduco-ai/backend/src
python -m evaluation.demo
```

You should see:
```
✓ All demos completed successfully!
```

## Step 2: List Available Datasets

```bash
python -m evaluation.run_evaluation --list-datasets
```

Output:
```
Available datasets:
  - tum_informatics_deadlines_factual.json
```

## Step 3: Run a Sample Evaluation (Demo Mode)

```bash
python -m evaluation.demo
```

This runs the evaluation with mock responses (no RAG pipeline needed).

## Step 4: Understand the Output

The evaluation calculates three metrics:

1. **Factual Accuracy** (0.0-1.0)
   - Checks if answer contains correct facts
   - Keywords: Required terms that must appear
   - Example: "May 31", "winter semester"

2. **Groundedness** (0.0-1.0)
   - Verifies answer is based on retrieved documents
   - Prevents hallucinations
   - Compares answer text with source documents

3. **Relevance** (0.0-1.0)
   - Checks if answer addresses the question
   - Detects unhelpful deflections
   - Example deflection: "Check the website"

**Overall Score** = weighted average of all metrics

## Step 5: Create Your First Test Case

Create `evaluation/datasets/my_first_test.json`:

```json
{
  "dataset_name": "my_first_test",
  "version": "1.0",
  "created": "2026-01-22",
  "source": "Custom test cases",
  
  "test_cases": [
    {
      "test_id": "test_001",
      "question": "What is TUM?",
      
      "metadata": {
        "question_type": "factual",
        "complexity_level": 1
      },
      
      "context": {
        "student_profile": null,
        "conversation_history": []
      },
      
      "expected_output": {
        "ground_truth": {
          "name": "Technical University of Munich"
        },
        "must_include_keywords": ["Technical University", "Munich"],
        "must_cite_sources": false
      },
      
      "evaluation_metrics": {
        "factual_accuracy": {
          "weight": 0.5,
          "threshold": 0.90
        },
        "groundedness": {
          "weight": 0.3,
          "threshold": 0.85
        },
        "relevance": {
          "weight": 0.2,
          "threshold": 0.80
        }
      }
    }
  ]
}
```

## Step 6: Run Your Test (When RAG Pipeline is Available)

```bash
# Note: This requires the full RAG pipeline to be initialized
# with GROQ_API_KEY and all dependencies
python -m evaluation.run_evaluation --dataset my_first_test
```

## Step 7: View Results

Results are saved in `evaluation/results/` with timestamps:
```
my_first_test_results_20260122_120000.json
```

View the file to see:
- Individual test results
- Metric scores
- Pass/fail status
- Summary statistics

## Common Commands

```bash
# List all datasets
python -m evaluation.run_evaluation --list-datasets

# Run evaluation (saves results)
python -m evaluation.run_evaluation --dataset DATASET_NAME

# Run evaluation (don't save results)
python -m evaluation.run_evaluation --dataset DATASET_NAME --no-save

# Run demo with mock chatbot
python -m evaluation.demo

# Test individual components
python -c "from evaluation.test_case_loader import TestCaseLoader; print('✓ Works!')"
```

## Understanding Test Results

### Example Output

```
======================================================================
FINAL RESULTS
======================================================================
Pass Rate: 50.0% (1/2)
Overall Score: 0.716
======================================================================
```

- **Pass Rate**: Percentage of tests that met all thresholds
- **Overall Score**: Average score across all tests

### Per-Test Metrics

```
--- Evaluation Results ---
Factual Accuracy: 1.000
  Keywords Found: ['May 31', 'winter semester']
  Keywords Missing: []

Groundedness: 0.950
  Grounded: True

Relevance: 0.900
  Is Deflection: False

Overall Score: 0.950
Test Passes: True
```

### Score Interpretation

- **0.90-1.00**: Excellent
- **0.80-0.89**: Good
- **0.70-0.79**: Fair
- **0.60-0.69**: Poor
- **<0.60**: Failing

## Troubleshooting

### "ModuleNotFoundError"
- Make sure you're in `backend/src/` directory
- Install dependencies: `pip install -r requirements.txt`

### "Dataset not found"
- Use `--list-datasets` to see available datasets
- Check filename (case-sensitive, include .json)

### "GROQ_API_KEY not found"
- Set environment variable: `export GROQ_API_KEY=your_key`
- Or add to `.env` file in `backend/src/rag/`
- Note: Not needed for `demo.py`

### Low Groundedness Scores
- Normal for mock data (demo mode)
- With real chatbot, check document retrieval
- May need to adjust similarity thresholds

## Next Steps

1. **Create More Test Cases**
   - Based on real user questions
   - Cover different complexity levels
   - Test edge cases

2. **Run Regular Evaluations**
   - After code changes
   - Before releases
   - Track improvements over time

3. **Analyze Failures**
   - Review failed tests
   - Identify patterns
   - Improve chatbot or data

4. **Customize Metrics**
   - Adjust weights per use case
   - Set appropriate thresholds
   - Add custom scoring rules

## Getting Help

- Read the full documentation: `evaluation/README.md`
- Check code examples in `evaluation/demo.py`
- Review sample dataset: `evaluation/datasets/tum_informatics_deadlines_factual.json`

## Summary

✓ Framework installed and tested
✓ Sample dataset available
✓ Demo mode works
✓ Ready to create custom test cases
✓ Ready to evaluate the chatbot

You're all set! 🚀
