import requests
import json
from django.conf import settings
from rest_framework.exceptions import APIException

class OpenRouterService:
    @staticmethod
    def analyze_content(content):
        """
        Sends content to OpenRouter for analysis using the configured model.
        """
        api_key = settings.OPENROUTER_API_KEY
        model = settings.OPENROUTER_MODEL
        
        if not api_key:
            raise APIException("OpenRouter API key is not configured.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Optional: Add site URL and name for OpenRouter rankings
            # "HTTP-Referer": "https://truthbot.example.com", 
            # "X-Title": "TruthBot",
        }

        prompt = f"""Analyze the reliability and truthfulness of the following content. 

Content: "{content}"

Provide your analysis in JSON format with these exact keys:
- "score": A number between 0-100 representing reliability (0=completely false, 50=uncertain, 100=completely true)
- "explanation": A brief explanation of your assessment

Consider factors like:
- Scientific consensus
- Verifiable facts
- Logical consistency
- Known misinformation patterns

Respond ONLY with valid JSON, no other text."""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a fact-checking AI that analyzes content reliability. Always respond with valid JSON containing 'score' (0-100) and 'explanation' fields."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            content_response = data['choices'][0]['message']['content']
            
            print(f"OpenRouter raw response: {content_response}")  # Debug logging
            
            # Parse the JSON response from the LLM
            try:
                # Try to extract JSON from response (might have extra text)
                content_clean = content_response.strip()
                
                # If response has markdown code blocks, extract JSON
                if '```json' in content_clean:
                    start = content_clean.find('```json') + 7
                    end = content_clean.find('```', start)
                    content_clean = content_clean[start:end].strip()
                elif '```' in content_clean:
                    start = content_clean.find('```') + 3
                    end = content_clean.find('```', start)
                    content_clean = content_clean[start:end].strip()
                
                result = json.loads(content_clean)
                score = result.get('score')
                explanation = result.get('explanation', 'No explanation provided')
                
                # Validate score is in valid range
                if score is not None:
                    score = max(0, min(100, float(score)))  # Clamp between 0-100
                else:
                    score = 50  # Default if no score
                
                print(f"Parsed score: {score}, explanation: {explanation[:100]}")  # Debug
                
                return {
                    'reliability_score': score,
                    'explanation': explanation
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"JSON parsing error: {e}")  # Debug
                # Fallback if LLM doesn't return valid JSON
                return {
                    'reliability_score': 50,  # Neutral score on error
                    'explanation': f"Analysis: {content_response[:500]}"  # Truncate long responses
                }
                
        except requests.RequestException as e:
            print(f"OpenRouter API error: {e}")  # Debug
            raise APIException(f"Error communicating with OpenRouter: {str(e)}")
