"""
tools/python_executor.py
========================
Executes dynamically generated Python code in a safe-ish environment.
This gives the AI agentic capabilities to solve complex tasks.
"""

import sys
import io
import traceback
from typing import Tuple

from core.logger import get_logger

logger = get_logger(__name__)


def execute_python(code: str) -> Tuple[bool, str]:
    """
    Executes a string of Python code and captures the standard output.

    Parameters
    ----------
    code : str
        The Python code to execute.

    Returns
    -------
    (success: bool, result_message: str)
    """
    if not code:
        return False, "❌ No code provided to execute."

    logger.info(f"Executing Python code:\\n{code}")

    # Create a string buffer to capture stdout
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()

    success = False
    result_msg = ""
    try:
        # Create a blank dictionary to act as the local namespace
        local_scope = {}
        exec(code, {}, local_scope)
        stdout_val = redirected_output.getvalue().strip()
        
        if stdout_val:
            result_msg = f"✅ Code executed successfully.\nOutput:\n{stdout_val}"
        else:
            result_msg = "✅ Code executed successfully (no output)."
        success = True

    except Exception as e:
        # Get the full traceback
        tb = traceback.format_exc()
        result_msg = f"❌ Execution failed:\n{tb}"
        logger.error(result_msg)
        success = False

    finally:
        # Restore normal stdout
        sys.stdout = old_stdout

    return success, result_msg
