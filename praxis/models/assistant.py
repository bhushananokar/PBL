# praxis/models/assistant.py
import os
import re
import json
import requests
from typing import Dict, List, Any, Optional, Tuple

from config import GROQ_API_URL, GROQ_DEFAULT_MODEL
from models.skill_analyzer import SkillAnalyzer

class EducationalCodeAssistant:
    def __init__(self, api_key: Optional[str] = None, db=None):
        """Initialize the Educational Code Assistant with Groq API key and database."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable or provide it as an argument.")
        
        # Set up API endpoint
        self.api_url = GROQ_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Model configurations
        self.llama3_70b = GROQ_DEFAULT_MODEL
        self.mixtral = GROQ_DEFAULT_MODEL
        
        # Database connection
        self.db = db
        
        # Initialize skill analyzer
        self.skill_analyzer = SkillAnalyzer(self)
    
    def _send_request(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 4000) -> Dict:
        """Send a request to the Groq API."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def enhance_prompt(self, user_prompt: str) -> str:
        """Use Groq to enhance and structure the user prompt for better code generation."""
        system_prompt = """
        You are an expert programming assistant. Your task is to:
        1. Analyze the user's coding request
        2. Structure and enhance it for optimal code generation
        3. Include specific requirements, edge cases, and expected functionality
        4. Format the output as a clear, detailed coding task
        5. Include code comments where helpful
        
        DO NOT generate any code yourself. Focus only on improving the prompt.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Enhance this coding prompt for better code generation: {user_prompt}"}
        ]
        
        response = self._send_request(self.mixtral, messages, temperature=0.3)
        
        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def generate_learning_challenge(self, enhanced_prompt: str) -> str:
        """Generate a learning challenge based on the user's request to encourage them to try themselves."""
        system_prompt = """
        You are an educational coding mentor. Given a programming problem:
        1. Break down the problem into logical steps
        2. Provide clear instructions on what the user should try to implement
        3. Mention key concepts, data structures, or algorithms they should consider
        4. Include 1-2 helpful tips or hints without directly giving away the solution
        5. Suggest resources they might reference for learning (documentation, specific methods, etc.)
        6. Encourage them to attempt the solution themselves
        7. Format your response conversationally as a supportive mentor would
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        response = self._send_request(self.mixtral, messages, temperature=0.4, max_tokens=4000)
        
        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def analyze_user_attempt(self, problem_description: str, user_code: str) -> str:
        """Analyze the user's code attempt and provide targeted feedback."""
        system_prompt = """
        You are an educational coding mentor reviewing a student's code attempt. Your goal is to provide constructive feedback:
        1. Identify what parts of the solution are correct and well-implemented
        2. Pinpoint specific issues or bugs in the code
        3. Suggest improvements without directly rewriting their code
        4. Explain conceptual misunderstandings if present
        5. Provide 2-3 specific hints that would help them improve their solution
        6. Be encouraging and supportive in your tone
        7. Do NOT provide complete code solutions
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Problem description: {problem_description}\n\nUser's code attempt:\n```\n{user_code}\n```\n\nPlease analyze this code attempt and provide educational feedback."}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.3, max_tokens=4000)
        
        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def generate_solution_flowchart(self, enhanced_prompt: str) -> str:
        """Generate a flowchart visualizing the solution approach."""
        system_prompt = """
        You are a programming educator. Create a detailed flowchart that:
        1. Breaks down the solution approach step-by-step
        2. Shows the logical flow of the algorithm
        3. Highlights key decision points and processes
        4. Is detailed enough to guide implementation without giving exact code
        5. Uses proper flowchart conventions
        6. Provide ONLY the Mermaid flowchart code without explanations
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a detailed solution flowchart for this problem:\n\n{enhanced_prompt}"}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.2, max_tokens=4000)
        
        if 'choices' in response and len(response['choices']) > 0:
            result = response['choices'][0]['message']['content']
            # Extract Mermaid code from the response
            mermaid_pattern = r'```mermaid\n([\s\S]*?)\n```'
            mermaid_match = re.search(mermaid_pattern, result)
            if mermaid_match:
                return mermaid_match.group(1)
            else:
                # Strip any other markdown formatting if present
                clean_pattern = r'```\n([\s\S]*?)\n```'
                clean_match = re.search(clean_pattern, result)
                if clean_match:
                    return clean_match.group(1)
                else:
                    return result
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def generate_code(self, enhanced_prompt: str) -> str:
        """Use Groq to generate code based on the enhanced prompt."""
        system_prompt = """
        You are an expert code generator creating educational code examples. Given a programming problem:
        1. Write clean, efficient, and well-documented code
        2. Include detailed comments explaining key concepts and your reasoning
        3. Handle edge cases and potential errors
        4. Follow best practices for the relevant language/framework
        5. Explain your implementation approach
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.2, max_tokens=8000)
        
        if 'choices' in response and len(response['choices']) > 0:
            # Clean up code - extract from markdown if needed
            return self._extract_code(response['choices'][0]['message']['content'])
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def _extract_code(self, text: str) -> str:
        """Extract code from markdown code blocks if present."""
        # Look for triple backtick code blocks
        code_pattern = r'```(?:\w+)?\n([\s\S]*?)\n```'
        code_matches = re.findall(code_pattern, text)
        
        if code_matches:
            # Join multiple code blocks with newlines
            return '\n\n'.join(code_matches)
        else:
            # Return the original text if no code blocks found
            return text
    
    def analyze_complexity(self, code: str) -> Dict[str, str]:
        """Use Groq to analyze time and space complexity of the code."""
        system_prompt = """
        You are an algorithm analysis expert. Analyze the provided code and:
        1. Determine its time complexity (Big O notation)
        2. Determine its space complexity (Big O notation)
        3. Explain the reasoning behind your analysis
        4. Consider best, average, and worst-case scenarios where applicable
        5. Format your response in plain text with clear sections for:
           - Time Complexity: [your analysis]
           - Space Complexity: [your analysis]
           - Explanation: [your explanation]
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze the time and space complexity of this code:\n\n{code}"}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.1, max_tokens=4000)
        
        if 'choices' in response and len(response['choices']) > 0:
            result = response['choices'][0]['message']['content']
            try:
                # Extract the time complexity
                time_complexity = self._extract_complexity(result, "time")
                
                # Extract the space complexity
                space_complexity = self._extract_complexity(result, "space")
                
                # Return results in a dictionary
                return {
                    "time_complexity": time_complexity,
                    "space_complexity": space_complexity,
                    "explanation": result
                }
            except Exception as e:
                return {
                    "time_complexity": "Analysis failed",
                    "space_complexity": "Analysis failed",
                    "explanation": f"Could not parse complexity analysis: {str(e)}\n\nPlease review the raw output: {result}"
                }
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def _extract_complexity(self, text: str, complexity_type: str) -> str:
        """Helper method to extract complexity from text."""
        patterns = [
            rf"{complexity_type}.*complexity.*O\([^)]+\)",
            rf"{complexity_type}.*O\([^)]+\)",
            r"O\([^)]+\)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return "Undefined"
    
    def review_code(self, code: str) -> Dict[str, Any]:
        """Use Groq to review code quality and suggest improvements."""
        system_prompt = """
        You are an expert code reviewer. Analyze the provided code and:
        1. Rate it on a scale of 1-10 for: readability, efficiency, robustness, and maintainability
        2. Identify specific strengths in the implementation
        3. Highlight areas for improvement with concrete suggestions
        4. Suggest optimizations for performance or resource usage
        5. Check for potential bugs, edge cases, or security issues
        6. Format as JSON with keys: overall_rating, strengths, improvements, optimizations, potential_issues
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review this code and suggest improvements:\n\n{code}"}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.3, max_tokens=6000)
        
        if 'choices' in response and len(response['choices']) > 0:
            result = response['choices'][0]['message']['content']
            try:
                # Try to extract JSON from the response
                json_pattern = r'\{[\s\S]*\}'
                json_match = re.search(json_pattern, result)
                if json_match:
                    json_str = json_match.group(0)
                    review = json.loads(json_str)
                else:
                    # If no JSON structure found, return the text response
                    review = {
                        "overall_rating": "N/A",
                        "review": result
                    }
                return review
            except Exception as e:
                return {
                    "overall_rating": "Review failed",
                    "review": f"Could not parse review: {str(e)}\n\nRaw response: {result}"
                }
        else:
            raise Exception("Failed to get a valid response from Groq API")
    
    def identify_challenge_skills(self, enhanced_prompt: str) -> Dict[str, float]:
        """Identify skills required for a challenge."""
        return self.skill_analyzer.analyze_problem(enhanced_prompt, enhanced_prompt)
    
    def score_user_attempt(self, user_code: str, model_solution: str, language: str) -> float:
        """Score a user's attempt compared to the model solution."""
        system_prompt = """
        You are an automated code grading system. Compare the user's code with the model solution and:
        1. Calculate a similarity score from 0.0 to 1.0
        2. Consider functionality over stylistic differences
        3. Check if key algorithms and approaches are implemented correctly
        4. Ignore minor differences in variable names, whitespace, etc.
        5. Return ONLY a number between 0 and 1 representing the score, with no explanation
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User's {language} code:\n```\n{user_code}\n```\n\nModel solution:\n```\n{model_solution}\n```\n\nPlease score the user's code from 0 to 1."}
        ]
        
        response = self._send_request(self.mixtral, messages, temperature=0.1, max_tokens=50)
        
        if 'choices' in response and len(response['choices']) > 0:
            result = response['choices'][0]['message']['content']
            try:
                # Extract just the numerical score
                score_pattern = r'([0-9]*\.?[0-9]+)'
                score_match = re.search(score_pattern, result)
                if score_match:
                    return float(score_match.group(0))
                else:
                    return 0.5  # Default score if parsing fails
            except Exception:
                return 0.5  # Default score
        else:
            return 0.5  # Default score
    
    def analyze_user_strengths_weaknesses(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Analyze a user's strengths and weaknesses based on their attempt history."""
        if not self.db:
            return None
        
        # Get user skills
        user_skills = self.db.get_user_skills(user_id)
        
        # Get weakest and strongest skills
        weak_skills = self.db.get_user_weakest_skills(user_id)
        strong_skills = self.db.get_user_strongest_skills(user_id)
        
        # Generate comprehensive analysis
        system_prompt = """
        You are an educational assessment expert. Based on a user's programming skills data:
        1. Analyze their strengths and weaknesses
        2. Identify patterns in their coding abilities
        3. Suggest specific areas to focus on for improvement
        4. Highlight strengths they can leverage
        5. Format your response in clear sections without being overly verbose
        """
        
        # Format skills data for the prompt
        strong_skills_str = "\n".join([f"- {name} (proficiency: {prof:.2f})" for _, name, _, prof in strong_skills])
        weak_skills_str = "\n".join([f"- {name} (proficiency: {prof:.2f})" for _, name, _, prof in weak_skills])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User's strongest skills:\n{strong_skills_str}\n\nUser's weakest skills:\n{weak_skills_str}\n\nPlease provide a comprehensive analysis of the user's coding strengths and weaknesses."}
        ]
        
        response = self._send_request(self.mixtral, messages, temperature=0.3, max_tokens=2000)
        
        if 'choices' in response and len(response['choices']) > 0:
            analysis = response['choices'][0]['message']['content']
            
            # Generate recommendations based on analysis
            recommendations = self.skill_analyzer.generate_recommendations(user_skills, weak_skills)
            
            return {
                "analysis": analysis,
                "recommendations": recommendations,
                "weak_skills": weak_skills,
                "strong_skills": strong_skills
            }
        else:
            return None
    
    def generate_personalized_learning_path(self, user_id: str, language: str) -> Optional[str]:
        """Generate a personalized learning path based on user's skills."""
        if not self.db:
            return None
        
        # Get user's weakest skills
        weak_skills = self.db.get_user_weakest_skills(user_id, limit=3)
        if not weak_skills:
            return None
        
        weak_skill_names = [name for _, name, _, _ in weak_skills]
        
        # Generate a learning path
        system_prompt = """
        You are an educational curriculum designer. Create a structured learning path to improve these programming skills:
        1. Design a progression of 5-7 coding challenges that build skills incrementally
        2. For each challenge, provide:
           - A clear title
           - A brief description of what to implement
           - The primary skill(s) it develops
           - Approximate difficulty (1-5)
        3. Order the challenges from easiest to hardest
        4. Format as a JSON array of challenge objects
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a learning path in {language} to improve these skills: {', '.join(weak_skill_names)}"}
        ]
        
        response = self._send_request(self.llama3_70b, messages, temperature=0.4, max_tokens=4000)
        
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            
            # Extract JSON
            try:
                json_pattern = r'\[[\s\S]*\]'
                json_match = re.search(json_pattern, content)
                if json_match:
                    path_json = json_match.group(0)
                    path_challenges = json.loads(path_json)
                    
                    # Create a learning path
                    path_title = f"Improving {', '.join(weak_skill_names[:2])}"
                    path_desc = f"A personalized learning path to improve skills in {', '.join(weak_skill_names)}"
                    
                    path_id = self.db.get_or_create_learning_path(path_title, path_desc, language)
                    
                    # Add challenges to the path
                    for i, challenge in enumerate(path_challenges):
                        # Create the challenge
                        challenge_desc = f"Create code in {language} that: {challenge['description']}"
                        enhanced_prompt = self.enhance_prompt(challenge_desc)
                        
                        challenge_id = self.db.store_challenge(
                            challenge['title'], 
                            enhanced_prompt, 
                            language, 
                            difficulty=challenge.get('difficulty', 2)
                        )
                        
                        # Map skills to challenge
                        if 'skills' in challenge:
                            skill_relevance = {skill: 0.8 for skill in challenge['skills']}
                            self.db.map_challenge_skills(challenge_id, skill_relevance)
                        
                        # Add to learning path
                        self.db.add_challenge_to_path(path_id, challenge_id, i)
                    
                    return path_id
            except Exception as e:
                print(f"Error creating learning path: {str(e)}")
                return None
        
        return None