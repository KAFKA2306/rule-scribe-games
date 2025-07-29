"""
AI Orchestrator - Multi-provider AI service with intelligent routing and fallback
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import structlog
from dataclasses import dataclass, field
import openai
import anthropic
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

from app.core.config import settings


logger = structlog.get_logger()


class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class TaskType(Enum):
    SUMMARIZATION = "summarization"
    QA = "qa"
    EXTRACTION = "extraction"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"


@dataclass
class AIRequest:
    """Request object for AI operations"""
    task_type: TaskType
    content: str
    prompt: str = ""
    max_tokens: int = 4000
    temperature: float = 0.1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResponse:
    """Response object from AI operations"""
    content: str
    provider: AIProvider
    model: str
    tokens_used: int = 0
    latency_ms: float = 0
    cost_estimate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, provider_type: AIProvider):
        self.provider_type = provider_type
        self.is_available = False
        self.error_count = 0
        self.last_error = None
        self.request_count = 0
        self.total_tokens = 0
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider"""
        pass
    
    @abstractmethod
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using the provider"""
        pass
    
    @abstractmethod
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using the provider"""
        pass
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get provider health status"""
        return {
            "provider": self.provider_type.value,
            "available": self.is_available,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "request_count": self.request_count,
            "total_tokens": self.total_tokens
        }


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider implementation"""
    
    def __init__(self):
        super().__init__(AIProvider.OPENAI)
        self.client = None
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
    
    async def initialize(self) -> bool:
        """Initialize OpenAI client"""
        try:
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI API key not provided")
                return False
            
            self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Test connection
            await self.client.models.list()
            self.is_available = True
            logger.info("OpenAI provider initialized successfully")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            logger.error("Failed to initialize OpenAI provider", error=str(e))
            return False
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using OpenAI"""
        start_time = time.time()
        
        try:
            system_prompt = self._get_system_prompt(request.task_type)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{request.prompt}\n\n{request.content}"}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=settings.TOP_P
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            self.request_count += 1
            tokens_used = response.usage.total_tokens
            self.total_tokens += tokens_used
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=self.provider_type,
                model=self.model,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                cost_estimate=self._estimate_cost(tokens_used),
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error("OpenAI generation failed", error=str(e))
            raise
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using OpenAI"""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            
            return [embedding.embedding for embedding in response.data]
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error("OpenAI embedding failed", error=str(e))
            raise
    
    def _get_system_prompt(self, task_type: TaskType) -> str:
        """Get system prompt based on task type"""
        prompts = {
            TaskType.SUMMARIZATION: "You are an expert at summarizing board game rules. Create clear, concise summaries that help players understand the game quickly.",
            TaskType.QA: "You are a board game rules expert. Answer questions about game rules clearly and accurately.",
            TaskType.EXTRACTION: "You are an expert at extracting structured information from board game rules.",
            TaskType.CLASSIFICATION: "You are an expert at classifying and categorizing board game content."
        }
        return prompts.get(task_type, "You are a helpful AI assistant specializing in board games.")
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on token usage"""
        # GPT-4 pricing (approximate)
        input_cost_per_1k = 0.03
        output_cost_per_1k = 0.06
        # Simplified calculation assuming 50/50 input/output
        return (tokens / 1000) * ((input_cost_per_1k + output_cost_per_1k) / 2)


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self):
        super().__init__(AIProvider.ANTHROPIC)
        self.client = None
        self.model = settings.ANTHROPIC_MODEL
    
    async def initialize(self) -> bool:
        """Initialize Anthropic client"""
        try:
            if not settings.ANTHROPIC_API_KEY:
                logger.warning("Anthropic API key not provided")
                return False
            
            self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.is_available = True
            logger.info("Anthropic provider initialized successfully")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            logger.error("Failed to initialize Anthropic provider", error=str(e))
            return False
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using Anthropic Claude"""
        start_time = time.time()
        
        try:
            system_prompt = self._get_system_prompt(request.task_type)
            
            response = await self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"{request.prompt}\n\n{request.content}"}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            self.request_count += 1
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            self.total_tokens += tokens_used
            
            return AIResponse(
                content=response.content[0].text,
                provider=self.provider_type,
                model=self.model,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                cost_estimate=self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens),
                metadata={"stop_reason": response.stop_reason}
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error("Anthropic generation failed", error=str(e))
            raise
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Anthropic doesn't provide embeddings, fallback to sentence-transformers"""
        # Use sentence-transformers as fallback
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts)
        return embeddings.tolist()
    
    def _get_system_prompt(self, task_type: TaskType) -> str:
        """Get system prompt based on task type"""
        prompts = {
            TaskType.SUMMARIZATION: "You are an expert at summarizing board game rules. Create clear, concise summaries that help players understand the game quickly. Focus on the core mechanics, setup, and win conditions.",
            TaskType.QA: "You are a board game rules expert. Answer questions about game rules clearly and accurately. Provide specific references to rule sections when possible.",
            TaskType.EXTRACTION: "You are an expert at extracting structured information from board game rules. Identify key game elements like player count, play time, components, and mechanics.",
            TaskType.CLASSIFICATION: "You are an expert at classifying and categorizing board game content. Identify genres, mechanics, themes, and complexity levels."
        }
        return prompts.get(task_type, "You are a helpful AI assistant specializing in board games.")
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on token usage"""
        # Claude pricing (approximate)
        input_cost_per_1k = 0.015
        output_cost_per_1k = 0.075
        return (input_tokens / 1000 * input_cost_per_1k) + (output_tokens / 1000 * output_cost_per_1k)


class GoogleProvider(BaseAIProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self):
        super().__init__(AIProvider.GOOGLE)
        self.model = None
        self.model_name = settings.GOOGLE_MODEL
    
    async def initialize(self) -> bool:
        """Initialize Google Gemini"""
        try:
            if not settings.GOOGLE_API_KEY:
                logger.warning("Google API key not provided")
                return False
            
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(self.model_name)
            self.is_available = True
            logger.info("Google provider initialized successfully")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            logger.error("Failed to initialize Google provider", error=str(e))
            return False
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using Google Gemini"""
        start_time = time.time()
        
        try:
            system_prompt = self._get_system_prompt(request.task_type)
            full_prompt = f"{system_prompt}\n\n{request.prompt}\n\n{request.content}"
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=settings.TOP_P
                )
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            self.request_count += 1
            tokens_used = response.usage_metadata.total_token_count if response.usage_metadata else 0
            self.total_tokens += tokens_used
            
            return AIResponse(
                content=response.text,
                provider=self.provider_type,
                model=self.model_name,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                cost_estimate=self._estimate_cost(tokens_used),
                metadata={"finish_reason": response.candidates[0].finish_reason.name if response.candidates else None}
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error("Google generation failed", error=str(e))
            raise
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using Google"""
        try:
            embeddings = []
            for text in texts:
                result = await asyncio.to_thread(
                    genai.embed_content,
                    model=settings.GOOGLE_EMBEDDING_MODEL,
                    content=text
                )
                embeddings.append(result['embedding'])
            return embeddings
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error("Google embedding failed", error=str(e))
            raise
    
    def _get_system_prompt(self, task_type: TaskType) -> str:
        """Get system prompt based on task type"""
        prompts = {
            TaskType.SUMMARIZATION: "You are an expert at summarizing board game rules. Create clear, concise summaries that help players understand the game quickly.",
            TaskType.QA: "You are a board game rules expert. Answer questions about game rules clearly and accurately.",
            TaskType.EXTRACTION: "You are an expert at extracting structured information from board game rules.",
            TaskType.CLASSIFICATION: "You are an expert at classifying and categorizing board game content."
        }
        return prompts.get(task_type, "You are a helpful AI assistant specializing in board games.")
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on token usage"""
        # Gemini pricing (approximate)
        cost_per_1k = 0.00025  # Very approximate
        return (tokens / 1000) * cost_per_1k


class AIOrchestrator:
    """
    Central orchestrator for managing multiple AI providers with intelligent routing
    """
    
    def __init__(self):
        self.providers: Dict[AIProvider, BaseAIProvider] = {}
        self.provider_priority = [AIProvider.OPENAI, AIProvider.ANTHROPIC, AIProvider.GOOGLE]
        self.task_routing: Dict[TaskType, List[AIProvider]] = {
            TaskType.SUMMARIZATION: [AIProvider.ANTHROPIC, AIProvider.OPENAI, AIProvider.GOOGLE],
            TaskType.QA: [AIProvider.OPENAI, AIProvider.ANTHROPIC, AIProvider.GOOGLE],
            TaskType.EXTRACTION: [AIProvider.OPENAI, AIProvider.GOOGLE, AIProvider.ANTHROPIC],
            TaskType.EMBEDDING: [AIProvider.OPENAI, AIProvider.GOOGLE],
            TaskType.CLASSIFICATION: [AIProvider.OPENAI, AIProvider.ANTHROPIC, AIProvider.GOOGLE]
        }
    
    async def initialize(self):
        """Initialize all available providers"""
        logger.info("Initializing AI Orchestrator")
        
        # Initialize providers
        self.providers[AIProvider.OPENAI] = OpenAIProvider()
        self.providers[AIProvider.ANTHROPIC] = AnthropicProvider()
        self.providers[AIProvider.GOOGLE] = GoogleProvider()
        
        # Initialize each provider
        initialization_tasks = [
            provider.initialize() for provider in self.providers.values()
        ]
        
        results = await asyncio.gather(*initialization_tasks, return_exceptions=True)
        
        available_providers = []
        for provider_type, result in zip(self.providers.keys(), results):
            if result is True:
                available_providers.append(provider_type.value)
            elif isinstance(result, Exception):
                logger.error(f"Failed to initialize {provider_type.value}", error=str(result))
        
        logger.info("AI Orchestrator initialized", available_providers=available_providers)
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """Generate text using the best available provider"""
        providers = self.task_routing.get(request.task_type, self.provider_priority)
        
        for provider_type in providers:
            provider = self.providers.get(provider_type)
            if provider and provider.is_available:
                try:
                    response = await provider.generate_text(request)
                    logger.info("Text generated successfully", 
                               provider=provider_type.value,
                               tokens=response.tokens_used,
                               latency=response.latency_ms)
                    return response
                except Exception as e:
                    logger.warning("Provider failed, trying next", 
                                 provider=provider_type.value, 
                                 error=str(e))
                    continue
        
        raise Exception("All AI providers failed or unavailable")
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using the best available provider"""
        embedding_providers = [AIProvider.OPENAI, AIProvider.GOOGLE]
        
        for provider_type in embedding_providers:
            provider = self.providers.get(provider_type)
            if provider and provider.is_available:
                try:
                    embeddings = await provider.create_embeddings(texts)
                    logger.info("Embeddings created successfully", 
                               provider=provider_type.value,
                               count=len(texts))
                    return embeddings
                except Exception as e:
                    logger.warning("Embedding provider failed, trying next", 
                                 provider=provider_type.value, 
                                 error=str(e))
                    continue
        
        # Fallback to sentence-transformers
        logger.info("Using sentence-transformers as fallback for embeddings")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts)
        return embeddings.tolist()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return {
            "orchestrator": "operational",
            "providers": {
                provider_type.value: provider.get_health_status()
                for provider_type, provider in self.providers.items()
            },
            "available_providers": [
                provider_type.value 
                for provider_type, provider in self.providers.items()
                if provider.is_available
            ]
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up AI Orchestrator")
        # Cleanup tasks if needed