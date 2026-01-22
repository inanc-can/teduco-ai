# LLM Evaluation Framework for Teduco-AI

A comprehensive evaluation framework for assessing the quality and accuracy of the Teduco-AI chatbot's responses.

## Overview

This framework provides tools to:
- Create and manage test case datasets
- Evaluate chatbot responses using multiple metrics
- Track evaluation results over time
- Identify areas for improvement

## Architecture

The evaluation framework consists of several key components:

### 1. **Chatbot Interface** (`chatbot_interface.py`)
Provides a clean API to query the RAG-based chatbot for evaluation purposes.

### 2. **Metrics** (`metrics.py`)
Implements three core evaluation metrics:

- **Factual Accuracy**: Measures whether the answer contains correct factual information
  - Checks for required keywords
  - Validates against ground truth data
  - Supports custom scoring rules

- **Groundedness**: Evaluates if the answer is based on retrieved documents
  - Compares answer content with source documents
  - Prevents hallucinations
  - Ensures citations are valid

- **Relevance**: Assesses if the answer addresses the question
  - Checks topic coverage
  - Detects deflection responses
  - Validates question-answer alignment

### 3. **Test Case Loader** (`test_case_loader.py`)
Handles loading and validation of test case datasets from JSON files.

### 4. **Evaluator** (`evaluator.py`)
Main orchestrator that:
- Runs test cases
- Calculates metrics
- Generates evaluation reports
- Saves results

### 5. **CLI Runner** (`run_evaluation.py`)
Command-line interface for running evaluations.

## Quick Start

### 1. List Available Datasets

```bash
cd /home/runner/work/teduco-ai/teduco-ai/backend/src
python -m evaluation.run_evaluation --list-datasets
```

### 2. Run an Evaluation

```bash
cd /home/runner/work/teduco-ai/teduco-ai/backend/src
python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual
```

### 3. View Results

Results are saved in `evaluation/results/` directory with timestamps.

## Test Case Format

Test cases are defined in JSON format. Here's the structure:

```json
{
  "dataset_name": "tum_informatics_deadlines_factual",
  "version": "1.0",
  "created": "2026-01-22",
  "source": "Description of data source",
  
  "test_cases": [
    {
      "test_id": "unique_test_identifier",
      "question": "What is the application deadline?",
      
      "metadata": {
        "question_type": "factual",
        "complexity_level": 1,
        "journey_phase": "research",
        "priority": "critical",
        "language": "english"
      },
      
      "context": {
        "student_profile": null,
        "conversation_history": [],
        "relevant_documents": ["path/to/source.json"]
      },
      
      "expected_output": {
        "ground_truth": {
          "deadline_winter": "May 31",
          "deadline_summer": "November 30"
        },
        "must_include_keywords": ["May 31", "winter semester"],
        "must_cite_sources": true,
        "must_include_details": [
          "Mention both semesters",
          "Specify application portal"
        ]
      },
      
      "evaluation_metrics": {
        "factual_accuracy": {
          "weight": 0.5,
          "threshold": 0.98,
          "scoring_rules": {
            "correct_date": 0.5,
            "correct_semester": 0.5
          }
        },
        "groundedness": {
          "weight": 0.3,
          "threshold": 0.95
        },
        "relevance": {
          "weight": 0.2,
          "threshold": 0.90
        }
      },
      
      "good_answer_example": "The deadline is May 31 for winter semester...",
      "bad_answer_examples": [
        {
          "answer": "Check the website",
          "why_bad": "Unhelpful deflection",
          "score": 0.1
        }
      ]
    }
  ]
}
```

## Creating New Test Cases

### 1. Create a JSON file in `evaluation/datasets/`

```bash
touch evaluation/datasets/my_new_test_set.json
```

### 2. Define test cases using the format above

### 3. Validate the dataset

```python
from evaluation.test_case_loader import TestCaseLoader

loader = TestCaseLoader()
dataset = loader.load_dataset('my_new_test_set')
# If this succeeds, your dataset is valid
```

### 4. Run the evaluation

```bash
python -m evaluation.run_evaluation --dataset my_new_test_set
```

## Metrics Details

### Factual Accuracy

Checks if the answer contains factually correct information based on:
- **Must-include keywords**: Essential terms that should appear
- **Ground truth data**: Expected facts from source documents
- **Scoring rules**: Custom weights for different aspects

**Score**: 0.0 - 1.0 (higher is better)

### Groundedness

Validates that the answer is based on retrieved documents:
- Compares answer sentences with source documents
- Uses sequence matching to detect paraphrasing
- Identifies potential hallucinations

**Score**: 0.0 - 1.0 (higher means more grounded)

### Relevance

Assesses if the answer addresses the question:
- Checks for keyword overlap between question and answer
- Detects deflection responses ("contact us", "check website")
- Validates topic coverage

**Score**: 0.0 - 1.0 (higher means more relevant)

### Overall Score

Weighted combination of all metrics:
```
overall = (factual * 0.5) + (groundedness * 0.3) + (relevance * 0.2)
```

Weights can be customized per test case.

## Integration Points

The framework integrates with these components:

### 1. Chatbot Query Function
Located in: `backend/src/routers/rag.py` → `/chat` endpoint

The framework uses:
- `RAGChatbotPipeline.answer_question()` for non-agentic queries
- `Agent.run()` for agentic queries with user context

### 2. Ground Truth Data
Located in: `backend/rag_data/*/`

Each program has a JSON file with metadata:
- `informatics-master-of-science-msc/informatics-master-of-science-msc.json`
- `mathematics-master-of-science-msc/mathematics-master-of-science-msc.json`

### 3. LLM Configuration
Model: **Groq llama-3.1-8b-instant** (configured in `rag/chatbot/pipeline.py`)

### 4. RAG Retrieval
Uses hybrid search combining:
- Semantic similarity (sentence transformers)
- Keyword matching (BM25-style)
- Stored in Supabase vector database

## Usage Examples

### Python API

```python
from evaluation.evaluator import Evaluator
from evaluation.chatbot_interface import ChatbotInterface

# Initialize
evaluator = Evaluator()

# Run evaluation
report = evaluator.evaluate_dataset('tum_informatics_deadlines_factual')

# Access results
print(f"Pass rate: {report['summary']['pass_rate']:.1%}")
print(f"Average score: {report['summary']['average_scores']['overall']:.3f}")

# Evaluate single test case
from evaluation.test_case_loader import TestCaseLoader

loader = TestCaseLoader()
dataset = loader.load_dataset('tum_informatics_deadlines_factual')
test_case = dataset['test_cases'][0]

result = evaluator.evaluate_test_case(test_case)
print(f"Test passed: {result['passes']}")
```

### Command Line

```bash
# List datasets
python -m evaluation.run_evaluation --list-datasets

# Run evaluation
python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual

# Run without saving results
python -m evaluation.run_evaluation --dataset tum_informatics_deadlines_factual --no-save

# Specify custom RAG data directory
python -m evaluation.run_evaluation --dataset my_dataset --data-dir /path/to/rag_data
```

## Sample Dataset

The framework includes a sample dataset: `tum_informatics_deadlines_factual.json`

This dataset contains test cases for:
- Application deadlines for TUM Informatics Master's
- Admission requirements
- Application process details

Test cases are based on actual data from:
`backend/rag_data/informatics-master-of-science-msc/informatics-master-of-science-msc.json`

## Interpreting Results

### Result Files

Saved in: `evaluation/results/{dataset}_results_{timestamp}.json`

Structure:
```json
{
  "dataset_name": "...",
  "evaluation_timestamp": "2026-01-22T12:00:00",
  "summary": {
    "total_tests": 2,
    "passed": 1,
    "failed": 1,
    "pass_rate": 0.5,
    "average_scores": {
      "overall": 0.85,
      "factual_accuracy": 0.90,
      "groundedness": 0.85,
      "relevance": 0.75
    }
  },
  "test_results": [...]
}
```

### Understanding Scores

- **0.90 - 1.00**: Excellent - Answer is accurate, grounded, and relevant
- **0.80 - 0.89**: Good - Minor issues, mostly correct
- **0.70 - 0.79**: Fair - Some inaccuracies or missing information
- **0.60 - 0.69**: Poor - Significant issues
- **< 0.60**: Failing - Major problems, incorrect or unhelpful

### Pass/Fail Criteria

A test case passes if ALL metrics meet their thresholds:
- Factual Accuracy ≥ threshold (typically 0.90-0.98)
- Groundedness ≥ threshold (typically 0.90-0.95)
- Relevance ≥ threshold (typically 0.85-0.90)

## Best Practices

### Creating Test Cases

1. **Use Real User Questions**: Base test cases on actual user queries
2. **Reference Ground Truth**: Link to source documents in the RAG data
3. **Set Realistic Thresholds**: Start with 0.85-0.90, adjust based on results
4. **Include Edge Cases**: Test boundary conditions and ambiguous queries
5. **Provide Examples**: Include both good and bad answer examples

### Running Evaluations

1. **Regular Testing**: Run evaluations after every major change
2. **Track Over Time**: Save all results to monitor improvements
3. **Analyze Failures**: Investigate why tests fail to improve the chatbot
4. **Iterate**: Update test cases as the chatbot evolves

### Improving Scores

- **Low Factual Accuracy**: Improve document quality, update ground truth data
- **Low Groundedness**: Adjust retrieval thresholds, improve chunking strategy
- **Low Relevance**: Refine prompts, improve question understanding

## Extending the Framework

### Adding New Metrics

Create a new method in `evaluation/metrics.py`:

```python
@staticmethod
def custom_metric(answer: str, **kwargs) -> Dict[str, Any]:
    """Your custom metric."""
    score = 0.0
    # Calculate score
    return {
        'score': score,
        'details': {...}
    }
```

### Custom Scoring Rules

Define in test case JSON:

```json
"scoring_rules": {
  "mentions_deadline": 0.4,
  "mentions_semester": 0.3,
  "mentions_portal": 0.3
}
```

## Troubleshooting

### "Dataset not found"
- Check that the JSON file exists in `evaluation/datasets/`
- Ensure filename matches (case-sensitive)
- Use `--list-datasets` to see available datasets

### "GROQ_API_KEY not found"
- Set the environment variable: `export GROQ_API_KEY=your_key`
- Or add to `.env` file in `backend/src/rag/`

### Low Groundedness Scores
- Check if documents are being retrieved
- Verify retrieval threshold is not too high
- Ensure embeddings are working correctly

### Tests Always Failing
- Review thresholds - they might be too strict
- Check ground truth data matches source documents
- Verify keywords are spelled correctly

## Contributing

To add new datasets:
1. Create JSON file in `evaluation/datasets/`
2. Follow the test case format
3. Validate with `TestCaseLoader`
4. Submit with documentation

## License

Part of the Teduco-AI project.
