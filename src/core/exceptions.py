"""
Custom exceptions for GovCon Capture Vibe.

Phase 1c: Exception Handling (#64)

These exceptions provide better error categorization and debugging
while maintaining the resilience pattern where code gracefully degrades
on failures rather than crashing.

Usage:
    from src.core.exceptions import (
        GovConError, 
        LLMError, 
        ConfigurationError,
        ExtractionError,
        InferenceError,
    )
"""

from typing import Optional


class GovConError(Exception):
    """Base exception for all GovCon Capture Vibe errors."""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.cause = cause
    
    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


class ConfigurationError(GovConError):
    """Raised when configuration is invalid or missing.
    
    Examples:
        - Missing required environment variables
        - Invalid LLM model configuration
        - Neo4j connection string malformed
    """
    pass


class LLMError(GovConError):
    """Raised when LLM API calls fail.
    
    Examples:
        - API rate limiting (429)
        - Model unavailable (503)
        - Invalid response format
        - Timeout
    """
    
    def __init__(
        self, 
        message: str, 
        cause: Optional[Exception] = None,
        model: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        super().__init__(message, cause)
        self.model = model
        self.status_code = status_code


class ExtractionError(GovConError):
    """Raised when entity/relationship extraction fails.
    
    Examples:
        - MinerU parsing failure
        - LightRAG chunking error
        - Output sanitization failure
    """
    
    def __init__(
        self, 
        message: str, 
        cause: Optional[Exception] = None,
        document: Optional[str] = None,
        chunk_id: Optional[str] = None
    ):
        super().__init__(message, cause)
        self.document = document
        self.chunk_id = chunk_id


class InferenceError(GovConError):
    """Raised when semantic inference algorithms fail.
    
    Examples:
        - Algorithm JSON parse failure
        - Relationship validation failure
        - Neo4j write failure
    """
    
    def __init__(
        self, 
        message: str, 
        cause: Optional[Exception] = None,
        algorithm: Optional[str] = None,
        entity_count: Optional[int] = None
    ):
        super().__init__(message, cause)
        self.algorithm = algorithm
        self.entity_count = entity_count


class StorageError(GovConError):
    """Raised when storage operations fail.
    
    Examples:
        - Neo4j connection failure
        - VDB persistence error
        - KV store corruption
    """
    
    def __init__(
        self, 
        message: str, 
        cause: Optional[Exception] = None,
        storage_type: Optional[str] = None,  # 'neo4j', 'vdb', 'kv_store'
        operation: Optional[str] = None      # 'read', 'write', 'connect'
    ):
        super().__init__(message, cause)
        self.storage_type = storage_type
        self.operation = operation


class PromptError(GovConError):
    """Raised when prompt loading or formatting fails.
    
    Examples:
        - Prompt file not found
        - Invalid prompt template
        - Missing required variables
    """
    
    def __init__(
        self, 
        message: str, 
        cause: Optional[Exception] = None,
        prompt_name: Optional[str] = None
    ):
        super().__init__(message, cause)
        self.prompt_name = prompt_name


class ValidationError(GovConError):
    """Raised when data validation fails.
    
    Examples:
        - Entity missing required fields
        - Invalid relationship source/target
        - Schema constraint violation
    """
    
    def __init__(
        self, 
        message: str, 
        cause: Optional[Exception] = None,
        entity_name: Optional[str] = None,
        field: Optional[str] = None
    ):
        super().__init__(message, cause)
        self.entity_name = entity_name
        self.field = field
