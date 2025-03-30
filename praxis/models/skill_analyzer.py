# praxis/models/skill_analyzer.py
import re
import json
from typing import Dict, List, Any, Optional

class SkillAnalyzer:
    """Class for analyzing code and identifying relevant skills."""
    
    def __init__(self, assistant):
        """Initialize the skill analyzer with an assistant for LLM capabilities."""
        self.assistant = assistant
    
    def analyze_problem(self, problem_description: str, enhanced_prompt: str) -> Dict[str, float]:
        """Analyze a problem to identify relevant skills."""
        system_prompt = """
        You are a programming education expert. Given a coding problem description:
        1. Identify the key programming skills and concepts required to solve it
        2. Rate each skill's relevance to the problem on a scale of 0.0 to 1.0
        3. Return a JSON object where keys are skill names and values are relevance scores
        4. Be specific but concise with skill names
        5. Include both general programming concepts and specific data structures/algorithms
        
        Example format:
        {
            "Arrays": 0.9,
            "String Manipulation": 0.7,
            "Dynamic Programming": 0.5
        }
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this coding problem and identify relevant skills with relevance scores:\n\n{enhanced_prompt}"}
        ]
        
        response = self.assistant._send_request(self.assistant.mixtral, messages, temperature=0.2, max_tokens=1000)
        
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            
            # Extract JSON
            try:
                # Find JSON in the response
                json_pattern = r'\{[\s\S]*\}'
                json_match = re.search(json_pattern, content)
                if json_match:
                    skills_json = json_match.group(0)
                    skills = json.loads(skills_json)
                    return skills
                else:
                    return {}
            except Exception as e:
                print(f"Error parsing skills: {str(e)}")
                return {}
        
        return {}
    
    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code to identify skills demonstrated and quality metrics."""
        system_prompt = """
        You are a code analysis expert. Given some code:
        1. Identify programming skills and concepts demonstrated in the code
        2. Rate each skill's mastery level on a scale of 0.0 to 1.0
        3. Provide an overall code quality score from 0.0 to 1.0
        4. Return results as a JSON object with these keys:
           - skills: Object mapping skill names to mastery scores
           - quality: Overall quality score
           - strengths: Array of specific strengths in the code
           - weaknesses: Array of specific areas for improvement
        
        Example format:
        {
            "skills": {
                "Arrays": 0.8,
                "Functions": 0.7,
                "Error Handling": 0.3
            },
            "quality": 0.6,
            "strengths": ["Good variable names", "Efficient algorithm"],
            "weaknesses": ["Missing error handling", "Could be more modular"]
        }
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this {language} code:\n\n{code}"}
        ]
        
        response = self.assistant._send_request(self.assistant.mixtral, messages, temperature=0.2, max_tokens=2000)
        
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            
            # Extract JSON
            try:
                # Find JSON in the response
                json_pattern = r'\{[\s\S]*\}'
                json_match = re.search(json_pattern, content)
                if json_match:
                    analysis_json = json_match.group(0)
                    analysis = json.loads(analysis_json)
                    return analysis
                else:
                    return {
                        "skills": {},
                        "quality": 0.5,
                        "strengths": [],
                        "weaknesses": []
                    }
            except Exception as e:
                print(f"Error parsing code analysis: {str(e)}")
                return {
                    "skills": {},
                    "quality": 0.5,
                    "strengths": [],
                    "weaknesses": []
                }
        
        return {
            "skills": {},
            "quality": 0.5,
            "strengths": [],
            "weaknesses": []
        }
    
    def generate_recommendations(self, user_skills: List, weak_skills: List) -> str:
        """Generate learning recommendations based on user skills."""
        # Format skills for the prompt
        weak_skills_str = "\n".join([f"- {name} (proficiency: {prof:.2f})" for _, name, _, prof in weak_skills])
        
        system_prompt = """
        You are a programming education expert. Based on a user's weakest skills:
        1. Recommend specific learning resources and exercises for improvement
        2. Suggest a learning path with concrete next steps
        3. Provide practical advice tailored to these specific skill gaps
        4. Format your response as a structured learning plan
        5. Include both theoretical resources and practical exercises
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The user needs to improve these skills:\n\n{weak_skills_str}\n\nPlease provide tailored learning recommendations."}
        ]
        
        response = self.assistant._send_request(self.assistant.llama3_70b, messages, temperature=0.4, max_tokens=2000)
        
        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']
        else:
            return "Could not generate recommendations."