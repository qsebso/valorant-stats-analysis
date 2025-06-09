"""
Utility functions such as rate limiting.

This module provides generic utilities used across the scraper,
currently focused on HTTP request rate limiting to be respectful
of the VLR.gg server.
"""

import time
import logging

# Set up module-level logger
logger = logging.getLogger(__name__)

# Fixed delay between requests in seconds
# This helps prevent overwhelming the server
REQUEST_DELAY = 1.0

def rate_limit() -> None:
    """
    Sleep to enforce a fixed request delay.
    
    This function is called before each HTTP request to ensure
    we maintain a minimum delay between requests. This helps
    prevent rate limiting and is respectful to the server.
    """
    logger.debug(f"Sleeping for {REQUEST_DELAY} seconds")
    time.sleep(REQUEST_DELAY) 