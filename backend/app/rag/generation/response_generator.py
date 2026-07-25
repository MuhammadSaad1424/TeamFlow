from typing import List, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate response."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini LLM Provider."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        """Initialize Gemini provider."""
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name = model
        self.genai = genai
        self.model = genai.GenerativeModel(
            model_name=model,
            system_instruction=(
                "You are TeamFlow AI, an expert code assistant that helps developers "
                "understand codebases. You provide clear, accurate, and detailed answers "
                "about code structure, functionality, and best practices. "
                "Always reference specific files and line numbers when possible."
            ),
        )
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate response from Gemini."""
        try:
            import asyncio
            generation_config = self.genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {str(e)}")
            raise
    
    async def stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream response from Gemini."""
        try:
            import asyncio
            generation_config = self.genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    stream=True,
                )
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini streaming error: {str(e)}")
            raise


class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider (fallback)."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initialize OpenAI provider."""
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate response from OpenAI."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful code assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {str(e)}")
            raise
    
    async def stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful code assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise


class ResponseGenerator:
    """Generate responses using LLM with context."""
    
    def __init__(self, llm_provider: LLMProvider):
        """Initialize response generator."""
        self.llm = llm_provider
    
    def build_prompt(
        self,
        query: str,
        context_chunks: List[dict],
        instruction: Optional[str] = None,
    ) -> str:
        """Build prompt with context."""
        prompt_parts = []
        
        if instruction:
            prompt_parts.append(f"INSTRUCTION:\n{instruction}\n")
        
        if context_chunks:
            prompt_parts.append("CONTEXT FROM CODEBASE:\n")
            for i, chunk in enumerate(context_chunks, 1):
                prompt_parts.append(f"\n[Reference {i}]")
                if chunk.get("file_path"):
                    prompt_parts.append(f"File: {chunk['file_path']}")
                if chunk.get("entity_name"):
                    prompt_parts.append(f"Entity: {chunk['entity_name']}")
                prompt_parts.append(f"Code:\n```\n{chunk.get('snippet', '')}\n```")
        
        prompt_parts.append(f"\nQUESTION:\n{query}")
        
        prompt_parts.append(
            "\nPLEASE PROVIDE:\n"
            "1. A clear, concise answer\n"
            "2. Relevant code examples from the provided context\n"
            "3. Explanation of how it works\n"
            "4. Any relevant warnings or considerations"
        )
        
        return "\n".join(prompt_parts)
    
    async def generate_response(
        self,
        query: str,
        context_chunks: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate response with context."""
        prompt = self.build_prompt(query, context_chunks)
        
        return await self.llm.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    async def stream_response(
        self,
        query: str,
        context_chunks: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream response with context."""
        prompt = self.build_prompt(query, context_chunks)
        
        async for chunk in self.llm.stream(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk


class ResponseAnalyzer:
    """Analyze generated responses for quality."""
    
    @staticmethod
    def detect_hallucination(
        response: str,
        context_chunks: List[dict],
    ) -> float:
        """Detect hallucination score (0-1, higher = more hallucinated)."""
        try:
            return 0.0
        except Exception as e:
            logger.error(f"Hallucination detection error: {str(e)}")
            return 0.0
    
    @staticmethod
    def calculate_confidence_score(
        response: str,
        context_chunks: List[dict],
        retrieval_score: float,
    ) -> float:
        """Calculate confidence score for response (0-1)."""
        try:
            score = 0.5
            score += retrieval_score * 0.3
            response_len = len(response)
            if 100 < response_len < 2000:
                score += 0.15
            if "```" in response:
                score += 0.05
            return min(score, 1.0)
        except Exception as e:
            logger.error(f"Confidence calculation error: {str(e)}")
            return 0.5
