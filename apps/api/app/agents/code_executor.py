import asyncio
import sys

async def execute_python_code(code: str, timeout: int = 10) -> str:
    """
    Executes Python code in a separate subprocess and captures stdout/stderr.
    Useful for SymPy math verification.
    """
    # Simple safety: don't allow os/subprocess imports
    if "import os" in code or "import subprocess" in code or "__import__('os')" in code:
        return "Error: unsafe imports detected (os/subprocess)."

    # Write code to a temporary file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file_path = f.name

    try:
        # Run the temporary file
        process = await asyncio.create_subprocess_exec(
            sys.executable, temp_file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return f"Error: Code execution timed out after {timeout} seconds."
            
        out_str = stdout.decode('utf-8').strip()
        err_str = stderr.decode('utf-8').strip()
        
        result = ""
        if out_str:
            result += f"Output:\n{out_str}\n"
        if err_str:
            result += f"Error:\n{err_str}\n"
            
        if not result:
            result = "Code executed successfully with no output."
            
        return result

    except Exception as e:
        return f"Execution Error: {str(e)}"
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
