"""
AI Service
Handles natural language processing, query parsing, and conversational AI
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from loguru import logger
import asyncio
import httpx # <-- FIX 2: Switched to httpx for async requests

# AI/ML imports
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available")

# Note: We are using httpx now, not requests
HUGGINGFACE_AVAILABLE = True

import numpy as np


class AIService:
    """
    Handles AI-powered natural language processing and conversational responses
    """

    def __init__(self):
        self.openai_client = None
        self.huggingface_api_key = None
        # FIX 1: Define the model name as a class attribute for easy changes
        self.huggingface_model = "mistralai/Mistral-7B-Instruct-v0.2"
        self.embedding_model = None
        self.setup_ai_services()

        # Predefined query patterns for prototype
        self.query_patterns = {
            'temperature': {'keywords': ['temperature', 'temp', 'thermal'], 'variable': 'TEMP'},
            'salinity': {'keywords': ['salinity', 'salt', 'psal'], 'variable': 'PSAL'},
            'pressure': {'keywords': ['pressure', 'depth', 'dbar'], 'variable': 'PRES'},
            'profile': {'keywords': ['profile', 'vertical plot'], 'operation': 'profile', 'viz_type': 'profile'},
            'average': {'keywords': ['average', 'mean', 'avg'], 'operation': 'mean'},
            'maximum': {'keywords': ['maximum', 'max', 'highest'], 'operation': 'max'},
            'minimum': {'keywords': ['minimum', 'min', 'lowest'], 'operation': 'min'}
        }

    def setup_ai_services(self):
        """
        Initialize AI services (OpenAI, Hugging Face, and local models)
        """
        try:
            if OPENAI_AVAILABLE:
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    self.openai_client = AsyncOpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized")
                else:
                    logger.warning("OPENAI_API_KEY not found in environment")
            
            self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
            if self.huggingface_api_key:
                logger.info("Hugging Face API key found, client initialized")
            else:
                logger.warning("HUGGINGFACE_API_KEY not found in environment")
            
            logger.info("Using mock embedding model for prototype")
        except Exception as e:
            logger.error(f"Error setting up AI services: {str(e)}")

    async def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language query into structured parameters.
        This version will use a pattern-based approach as a reliable default.
        """
        try:
            logger.info(f"Parsing query: {query}")
            query_lower = query.lower()
            
            # Start with pattern matching as a base
            parsed = self._parse_with_patterns(query_lower)
            
            # Extract depth information using a more robust regex
            depth_matches = re.findall(r'(\d+)\s*(m|meters|dbar|db)\b', query_lower)
            if depth_matches:
                # Use the last found depth number
                depth = int(depth_matches[-1][0])
                parsed['depth_range'] = [max(0, depth - 100), depth + 100]

            # If any words suggest a profile, set the operation and viz_type
            if any(word in query_lower for word in self.query_patterns['profile']['keywords']):
                 parsed['operation'] = 'profile'
                 parsed['viz_type'] = 'profile'

            logger.info(f"Parsed query result: {parsed}")
            return parsed

        except Exception as e:
            logger.error(f"Error parsing query: {str(e)}")
            return {'error': str(e)}

    def _parse_with_patterns(self, query_lower: str) -> Dict[str, Any]:
        """Fallback pattern matching for query parsing."""
        parsed = {'variable': 'TEMP', 'operation': 'mean', 'viz_type': 'table'}
        
        # This logic prioritizes the last found keyword for each category
        for key, pattern in self.query_patterns.items():
            if any(keyword in query_lower for keyword in pattern['keywords']):
                if 'variable' in pattern:
                    parsed['variable'] = pattern['variable']
                if 'operation' in pattern:
                    parsed['operation'] = pattern['operation']
                if 'viz_type' in pattern:
                    parsed['viz_type'] = pattern['viz_type']
        return parsed

    async def generate_response(self, original_query: str, data_result: Dict[str, Any], parsed_query: Dict[str, Any]) -> str:
        """
        Generate conversational response based on query results.
        """
        try:
            if not data_result.get('success', False):
                return f"I'm sorry, I couldn't process your query. Error: {data_result.get('error', 'Unknown')}"
            
            # Use Hugging Face if available
            if self.huggingface_api_key:
                try:
                    return await self._generate_with_huggingface(original_query, data_result, parsed_query)
                except Exception as e:
                    logger.warning(f"Hugging Face generation failed: {e}. Falling back to templates.")
            
            # Fallback to template-based responses
            return self._generate_template_response(original_query, data_result, parsed_query)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I found some data but encountered an error trying to explain it."

    async def _generate_with_huggingface(self, original_query: str, data_result: Dict[str, Any], parsed_query: Dict[str, Any]) -> str:
        """Generate response using Hugging Face with httpx."""
        var_name = data_result.get('metadata', {}).get('long_name', 'data')
        operation = parsed_query.get('operation', 'analysis')
        data_value = data_result.get('data')
        units = data_result.get('metadata', {}).get('units', '')

        prompt = f"""
As a friendly oceanographer AI, explain this ARGO float data result to a user.
User asked: "{original_query}"
Data found: The {operation} of {var_name} is {data_value} {units}.
Generate a concise, friendly, and informative response in one or two sentences:
"""
        api_url = f"https://api-inference.huggingface.co/models/{self.huggingface_model}"
        headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.7, "return_full_text": False}}

        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=payload, timeout=20.0)
        
        if response.status_code == 200:
            result = response.json()
            if result and isinstance(result, list):
                generated_text = result[0].get('generated_text', '').strip()
                if generated_text:
                    logger.info("Hugging Face generated response successfully")
                    return generated_text
            raise Exception("Invalid or empty response format from Hugging Face")
        else:
            logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
            raise Exception(f"API call failed with status {response.status_code}")

    def _generate_template_response(self, original_query: str, data_result: Dict[str, Any], parsed_query: Dict[str, Any]) -> str:
        """Generate response using templates (fallback)."""
        metadata = data_result.get('metadata', {})
        var_name = metadata.get('long_name', 'data').lower()
        operation = parsed_query.get('operation', 'analysis')
        data = data_result.get('data')
        units = metadata.get('units', '')

        if operation == 'mean' and isinstance(data, (int, float)):
            return f"Based on the data, the average {var_name} is {data:.2f} {units}."
        elif operation == 'max' and isinstance(data, (int, float)):
            return f"The maximum {var_name} recorded is {data:.2f} {units}."
        elif operation == 'min' and isinstance(data, (int, float)):
            return f"The minimum {var_name} found is {data:.2f} {units}."
        elif operation == 'profile':
            return f"I've retrieved a {var_name} profile. It shows how the value changes with ocean depth."
        else:
            return "I've processed your query and the data is ready for viewing."
    
    # Other methods like get_embeddings, suggest_follow_up_queries can remain as they are.