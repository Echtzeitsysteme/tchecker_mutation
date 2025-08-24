import subprocess
import os
import sys
import json
import ast
from typing import List, Tuple, Any
import tempfile
from typing import Optional

def call_tchecker_function_in_new_process(
    func_name: str,
    argtypes: List[str],
    has_result: bool,
    args: List[Any],
    lib_path: str = "./libtchecker.so",
    caller_script: str = "./util/tchecker_caller.py"
) -> Tuple[str, Optional[str]]:
    """
    Calls a function in a fresh Python subprocess by invoking tchecker_caller.py.

    Returns stdout_output (everything before the final line)
    and result (parsed from the final line).
    """

    result_filename = None
    # If the function has a result the result gets written to a file with the file name passed as the first argument
    if has_result:
        # Create a temporary file to store the result
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            result_filename = temp_file.name
            print(f"Temporary file created: {result_filename}")
            args = [result_filename] + args
            argtypes = ["ctypes.c_char_p"] + argtypes

    args_json     = json.dumps(args)
    argtypes_json = json.dumps(argtypes)

    cmd = [
        sys.executable,
        caller_script,
        "--lib-path", lib_path,
        "--func-name", func_name,
        "--argtypes", argtypes_json,
        "--args", args_json,
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if proc.returncode != 0:
        print(proc.stdout)
        print(f"Error calling tchecker function: {proc.stderr.strip()}")
        raise RuntimeError(f"Child process failed: {proc.stderr.strip()} {proc.returncode}")

    print(proc.stderr.strip())
    result = None
    if result_filename:
        print(f"Reading result from: {result_filename}")
        with open(result_filename, "r") as result_file:
            result = result_file.read()
        # Remove the temporary file
        # os.remove(result_filename)

    return proc.stdout, result