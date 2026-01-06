"""
Logging Configuration for GovCon Capture Vibe

Sets up structured logging with both file and console output.
Prevents terminal overflow by using rotating log files.

Features:
- Dedicated processing.log for RFP processing (RAG-Anything, LightRAG, semantic inference)
- Filtered console output (no HTTP health check spam)
- Separate error logging
- Automatic log rotation (10MB files, 5 backups per log)
- No duplicate log entries

Log Files Created:
    logs/processing.log - RFP extraction, entity/relationship counts, semantic inference progress
    logs/server.log - Server startup, API calls, configuration
    logs/errors.log - All errors from any component
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# ANSI COLOR CODES (Centralized - DRY)
# ═══════════════════════════════════════════════════════════════════════════════
# Use these module-level constants instead of redefining in each file

class Colors:
    """ANSI color codes for terminal output."""
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def log_banner(
    title: str,
    items: Optional[List[Tuple[str, str]]] = None,
    width: int = 80,
    emoji: str = "",
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log a standardized banner with title and optional items.
    
    Usage:
        from src.utils.logging_config import log_banner, Colors
        
        log_banner("🎯 CONFIGURATION", [
            ("Entity Types", "18 specialized"),
            ("Parser", "MinerU 2.6.4"),
        ])
    
    Args:
        title: Banner title (can include emoji)
        items: Optional list of (label, value) tuples to display
        width: Banner width in characters (default: 80)
        emoji: Optional emoji prefix (deprecated - include in title instead)
        logger: Logger instance (defaults to root logger)
    """
    if logger is None:
        logger = logging.getLogger()
    
    c = Colors
    separator = f"{c.CYAN}{'═' * width}{c.RESET}"
    
    logger.info("")
    logger.info(separator)
    logger.info(f"{c.BOLD}{c.MAGENTA}{title}{c.RESET}")
    logger.info(separator)
    
    if items:
        for label, value in items:
            logger.info(f"{c.GREEN}{label}:{c.RESET} {value}")
    
    logger.info(separator)
    logger.info("")


class HTTPFilter(logging.Filter):
    """Filter out repetitive HTTP health check logs from console"""
    
    def filter(self, record):
        # Filter out uvicorn access logs
        if record.name == "uvicorn.access":
            return False
        
        # Filter out health check spam
        message = record.getMessage()
        health_patterns = [
            "GET /health",
            "POST /health",
            "GET /api/health",
            "200 OK",
            "::1:",  # IPv6 localhost requests
            "127.0.0.1:",  # IPv4 localhost requests
        ]
        
        for pattern in health_patterns:
            if pattern in message:
                return False
        
        return True


class ProcessingFilter(logging.Filter):
    """Filter to capture RFP processing logs (RAG-Anything, LightRAG, semantic inference)"""
    
    def filter(self, record):
        # Capture logs from processing components
        processing_loggers = [
            "lightrag",
            "raganything",
            "src.server.routes",  # Our processing pipeline
            "src.inference",  # Semantic inference (entity correction, relationship inference, metadata enrichment)
            "src.ingestion",  # Document ingestion
        ]
        
        for logger_name in processing_loggers:
            if record.name.startswith(logger_name):
                return True
        
        # Capture key processing messages regardless of logger
        processing_keywords = [
            "Processing",
            "entities",
            "relationships",
            "semantic",
            "GraphML",
            "Neo4j",
            "inference",
            "enrichment",
            "parsing",
            "extraction",
        ]
        
        message = record.getMessage()
        for keyword in processing_keywords:
            if keyword in message:
                return True
        
        return False


class ServerFilter(logging.Filter):
    """Filter for server logs (startup, config, API calls - excluding processing details)"""
    
    def filter(self, record):
        # Exclude processing logs from server log
        processing_loggers = [
            "lightrag.llm",  # LLM calls
            "lightrag.kg",   # Knowledge graph operations
            "raganything",
        ]
        
        for logger_name in processing_loggers:
            if record.name.startswith(logger_name):
                return False
        
        return True


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
):
    """
    Set up comprehensive logging with clean separation of concerns.
    
    Log Files:
        - processing.log: RFP extraction, entities, relationships, semantic inference details
        - server.log: Server startup, initialization, API endpoints
        - errors.log: All errors from any source
    
    Console Output:
        - Filtered to show important messages (no health check spam)
        - Shows RFP processing progress
        - Shows errors and warnings
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files (default: "logs")
        max_file_size: Maximum size per log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        console_output: Whether to output to console (default: True)
    
    Returns:
        dict: Paths to created log files
    """
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )
    
    # ========================================================================
    # 1. PROCESSING.LOG - RFP processing details
    # ========================================================================
    processing_log_file = log_path / "processing.log"
    processing_handler = logging.handlers.RotatingFileHandler(
        processing_log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    processing_handler.setLevel(logging.INFO)
    processing_handler.setFormatter(detailed_formatter)
    processing_handler.addFilter(ProcessingFilter())
    root_logger.addHandler(processing_handler)
    
    # CRITICAL: LightRAG's logger has propagate=False, so we must add our handler directly
    # This captures "Chunk X of N extracted" messages from lightrag.operate (Branch 040 pattern)
    lightrag_logger = logging.getLogger("lightrag")
    lightrag_logger.addHandler(processing_handler)
    
    # Also capture raganything logs (multimodal processing)
    raganything_logger = logging.getLogger("raganything")
    raganything_logger.addHandler(processing_handler)
    
    # ========================================================================
    # 2. SERVER.LOG - Server operations
    # ========================================================================
    server_log_file = log_path / "server.log"
    server_handler = logging.handlers.RotatingFileHandler(
        server_log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    server_handler.setLevel(logging.INFO)
    server_handler.setFormatter(detailed_formatter)
    server_handler.addFilter(ServerFilter())
    root_logger.addHandler(server_handler)
    
    # ========================================================================
    # 3. ERRORS.LOG - All errors
    # ========================================================================
    error_log_file = log_path / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # ========================================================================
    # 4. CONSOLE OUTPUT - Filtered (no health check spam)
    # ========================================================================
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(HTTPFilter())
        root_logger.addHandler(console_handler)
    
    # Log startup message using centralized banner utility
    logger = logging.getLogger(__name__)
    c = Colors
    
    log_banner("📋 LOGGING INFRASTRUCTURE", logger=logger)
    logger.info(f"{c.YELLOW}Directory:{c.RESET}        {log_path.absolute()}")
    logger.info(f"{c.GREEN}Processing Log:{c.RESET}   {processing_log_file.name} {c.CYAN}(RFP extraction, semantic inference){c.RESET}")
    logger.info(f"{c.GREEN}Server Log:{c.RESET}       {server_log_file.name} {c.CYAN}(startup, API calls){c.RESET}")
    logger.info(f"{c.GREEN}Error Log:{c.RESET}        {error_log_file.name} {c.CYAN}(all errors){c.RESET}")
    logger.info(f"{c.YELLOW}Max File Size:{c.RESET}    {max_file_size / 1024 / 1024:.1f}MB per file")
    logger.info(f"{c.YELLOW}Backup Count:{c.RESET}     {backup_count} files per log")
    logger.info(f"{c.YELLOW}Console Output:{c.RESET}   {'Enabled' if console_output else 'Disabled'} (filtered)")
    logger.info(f"{c.YELLOW}Log Level:{c.RESET}        {log_level.upper()}")
    logger.info(f"{c.CYAN}{'═' * 80}{c.RESET}")
    logger.info("")
    
    return {
        "log_dir": str(log_path.absolute()),
        "processing_log": str(processing_log_file),
        "server_log": str(server_log_file),
        "error_log": str(error_log_file),
    }


def log_graceful_failure(logger: logging.Logger, operation: str, error: Exception, context: str = "") -> None:
    """
    Log a graceful failure with truncated error message (non-critical, processing continues).
    
    Use this for expected failures that should not crash the system:
    - Table extraction failures (3-5% tolerance)
    - Relationship inference failures
    - Individual chunk processing failures
    
    Args:
        logger: Logger instance to use
        operation: Brief description of what failed (e.g., "Table extraction", "Relationship inference")
        error: The exception that was caught
        context: Optional context (e.g., chunk_id, table_id) to include in log
    
    Example:
        try:
            result = process_table(...)
        except Exception as e:
            log_graceful_failure(logger, "Table extraction", e, chunk_id)
            return empty_result()
    """
    error_msg = str(error)[:100]  # Truncate to 100 chars
    if context:
        logger.warning(f"⚠️ {operation} failed ({context}): {error_msg} - continuing with degraded result")
    else:
        logger.warning(f"⚠️ {operation} failed: {error_msg} - continuing with degraded result")


def get_log_summary(log_dir: str = "logs") -> dict:
    """Get summary of current log files with sizes and timestamps"""
    log_path = Path(log_dir)
    
    if not log_path.exists():
        return {"error": "Log directory does not exist"}
    
    log_files = []
    for log_file in sorted(log_path.glob("*.log*")):
        try:
            stat = log_file.stat()
            log_files.append({
                "name": log_file.name,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                "path": str(log_file.absolute())
            })
        except Exception as e:
            log_files.append({
                "name": log_file.name,
                "error": str(e)
            })
    
    return {
        "log_directory": str(log_path.absolute()),
        "total_files": len(log_files),
        "files": log_files
    }
