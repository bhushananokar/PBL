# utils/completion_utils.py
import re
import json
from typing import Dict, Any, Tuple, List, Optional

def evaluate_completion(
    code: str, 
    solution: str, 
    score: float, 
    difficulty: int,
    code_quality: Optional[Dict[str, Any]] = None,
    test_results: Optional[Dict[str, bool]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Evaluate whether a coding attempt should be marked as completed/successful.
    
    Args:
        code: User's code
        solution: Model solution
        score: Similarity score (0-1)
        difficulty: Challenge difficulty (1-5)
        code_quality: Optional code quality metrics
        test_results: Optional test case results
        
    Returns:
        Tuple containing:
            - Boolean indicating if attempt is successful
            - Dictionary with detailed evaluation metrics
    """
    # Define difficulty-based thresholds
    # Higher difficulty = lower threshold required
    difficulty_thresholds = {
        1: 0.85,  # Easy challenges need high similarity
        2: 0.80,
        3: 0.75,
        4: 0.70,
        5: 0.65   # Difficult challenges allow more divergence
    }
    
    # Get threshold for this difficulty level (default to 0.8)
    score_threshold = difficulty_thresholds.get(difficulty, 0.8)
    
    # Initialize evaluation metrics
    evaluation = {
        "score": score,
        "score_threshold": score_threshold,
        "passes_score_threshold": score >= score_threshold,
        "difficulty": difficulty,
        "code_length_ratio": len(code) / max(1, len(solution)),
        "test_cases_passed": 0,
        "total_test_cases": 0,
        "all_tests_passed": False,
        "code_quality_sufficient": True,
    }
    
    # Handle test results if provided
    if test_results:
        evaluation["total_test_cases"] = len(test_results)
        evaluation["test_cases_passed"] = sum(1 for result in test_results.values() if result)
        evaluation["all_tests_passed"] = all(test_results.values())
    
    # Handle code quality metrics if provided
    if code_quality:
        if "quality" in code_quality:
            evaluation["code_quality_score"] = code_quality["quality"]
            evaluation["code_quality_sufficient"] = code_quality["quality"] >= 0.5
    
    # Check if code is too short (possibly incomplete)
    is_too_short = evaluation["code_length_ratio"] < 0.3
    evaluation["is_too_short"] = is_too_short
    
    # Check for placeholder or comment-only code
    has_actual_code = bool(re.search(r'[^\s#]', code))
    evaluation["has_actual_code"] = has_actual_code
    
    # Determine if successful based on multiple criteria
    is_successful = (
        evaluation["passes_score_threshold"] and
        not is_too_short and 
        has_actual_code and
        evaluation["code_quality_sufficient"]
    )
    
    # If we have test results, they must pass for success
    if test_results:
        is_successful = is_successful and evaluation["all_tests_passed"]
    
    evaluation["is_successful"] = is_successful
    
    return is_successful, evaluation

def evaluate_test_cases(code: str, test_cases: List[Dict[str, Any]], lang: str) -> Dict[str, bool]:
    """
    Evaluate the user's code against test cases.
    This is a placeholder - in a real system, we would actually execute the code.
    
    Args:
        code: User's code
        test_cases: List of test cases with inputs and expected outputs
        lang: Programming language
        
    Returns:
        Dictionary mapping test case IDs to boolean results
    """
    # In a real system, we would execute the code against test cases
    # For now, we'll simulate results based on code patterns
    
    results = {}
    
    # Very simplistic check - just makes sure test case keys appear in the code
    # In a real system, we would actually run the code
    for i, test_case in enumerate(test_cases):
        test_id = f"test_{i+1}"
        
        # Check if input values appear in the code (very primitive check)
        input_present = all(str(inp) in code for inp in test_case["inputs"])
        output_present = str(test_case["expected_output"]) in code
        
        # Check for specific function handling based on language
        function_patterns = {
            "python": r"def\s+\w+\s*\([^)]*\)",
            "javascript": r"function\s+\w+\s*\([^)]*\)",
            "java": r"\w+\s+\w+\s*\([^)]*\)\s*\{",
            "cpp": r"\w+\s+\w+\s*\([^)]*\)\s*\{",
        }
        
        has_function = bool(re.search(function_patterns.get(lang, r"function"), code))
        
        # Primitive assessment - in reality, would execute the code
        # and compare actual outputs to expected outputs
        results[test_id] = has_function and (input_present or output_present)
    
    return results

def generate_test_cases(problem_description: str, solution: str, assistant) -> List[Dict[str, Any]]:
    """
    Generate test cases for a coding problem.
    
    Args:
        problem_description: The problem description
        solution: The model solution
        assistant: The LLM assistant to use for test case generation
        
    Returns:
        List of test cases with inputs and expected outputs
    """
    system_prompt = """
    You are a test case generator for coding problems. Given a problem description and solution:
    1. Create 3-5 test cases that verify the solution works correctly
    2. Include a variety of inputs: typical cases, edge cases, and corner cases
    3. For each test case, provide:
       - Input values
       - Expected output
       - A brief explanation of what the test case is checking
    4. Format your response as a JSON array of test objects
    
    Example format:
    [
        {
            "inputs": [5, 10],
            "expected_output": 15,
            "description": "Basic case - sum of two positive integers"
        },
        {
            "inputs": [-3, 3],
            "expected_output": 0,
            "description": "Edge case - sum of positive and negative that cancel out"
        }
    ]
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Problem:\n{problem_description}\n\nSolution:\n{solution}\n\nPlease generate test cases for this problem."}
    ]
    
    response = assistant._send_request(assistant.mixtral, messages, temperature=0.3, max_tokens=2000)
    
    if 'choices' in response and len(response['choices']) > 0:
        result = response['choices'][0]['message']['content']
        
        # Try to extract JSON array
        json_pattern = r'\[[\s\S]*\]'
        json_match = re.search(json_pattern, result)
        
        if json_match:
            try:
                test_cases = json.loads(json_match.group(0))
                return test_cases
            except json.JSONDecodeError:
                pass
    
    # Default test cases if generation fails
    return [
        {
            "inputs": ["sample_input"],
            "expected_output": "sample_output",
            "description": "Basic test case"
        }
    ]