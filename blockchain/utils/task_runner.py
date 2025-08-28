"""
Task execution utility with fallback mechanism
=============================================

This module provides a reliable way to execute blockchain tasks with automatic
fallback from Celery to direct execution if Celery is not available.
"""

import logging
from functools import wraps
from django.conf import settings

logger = logging.getLogger(__name__)

def execute_task_with_fallback(task_func, *args, **kwargs):
    """
    Execute a task with fallback mechanism.
    
    First tries to execute via Celery (.delay()), if that fails,
    falls back to direct execution.
    
    Args:
        task_func: The Celery task function
        *args: Arguments to pass to the task
        **kwargs: Keyword arguments to pass to the task
    
    Returns:
        dict: Result information with keys:
            - success: bool
            - method: 'celery' or 'direct'
            - result: The actual result or error message
            - task_id: Celery task ID (if using Celery)
    """
    # Try Celery first
    try:
        logger.info(f"Attempting Celery execution for task: {task_func.__name__}")
        celery_result = task_func.delay(*args, **kwargs)
        
        return {
            'success': True,
            'method': 'celery',
            'result': celery_result,
            'task_id': celery_result.id,
            'message': f"Task submitted to Celery with ID: {celery_result.id}"
        }
        
    except Exception as celery_error:
        logger.warning(f"Celery execution failed for {task_func.__name__}: {celery_error}")
        
        # Fallback to direct execution
        try:
            logger.info(f"Falling back to direct execution for task: {task_func.__name__}")
            direct_result = task_func(*args, **kwargs)
            
            return {
                'success': True,
                'method': 'direct',
                'result': direct_result,
                'task_id': None,
                'message': f"Task executed directly: {direct_result}"
            }
            
        except Exception as direct_error:
            logger.error(f"Direct execution also failed for {task_func.__name__}: {direct_error}")
            
            return {
                'success': False,
                'method': 'failed',
                'result': None,
                'task_id': None,
                'message': f"Both Celery and direct execution failed: {direct_error}"
            }

def task_with_fallback(task_func):
    """
    Decorator that adds fallback functionality to a task function.
    
    Usage:
        @task_with_fallback
        def my_task():
            # task logic here
            pass
    """
    @wraps(task_func)
    def wrapper(*args, **kwargs):
        return execute_task_with_fallback(task_func, *args, **kwargs)
    return wrapper

def safe_task_execution(task_func, *args, **kwargs):
    """
    Safe task execution that handles errors gracefully.
    
    This is a simpler version that just returns success/failure
    without detailed result information.
    
    Args:
        task_func: The task function to execute
        *args: Arguments for the task
        **kwargs: Keyword arguments for the task
    
    Returns:
        bool: True if task executed successfully (via any method), False otherwise
    """
    result = execute_task_with_fallback(task_func, *args, **kwargs)
    return result['success']

def get_task_status_message(result_dict):
    """
    Get a user-friendly message from a task execution result.
    
    Args:
        result_dict: Result dictionary from execute_task_with_fallback
    
    Returns:
        str: User-friendly status message
    """
    if result_dict['success']:
        if result_dict['method'] == 'celery':
            return f"Task submitted to background processing. Task ID: {result_dict['task_id']}"
        elif result_dict['method'] == 'direct':
            return f"Task completed successfully: {result_dict['message']}"
    else:
        return f"Task failed: {result_dict['message']}"
    
    return "Unknown task status"
