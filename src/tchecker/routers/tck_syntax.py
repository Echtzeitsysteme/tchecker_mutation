import tempfile
import os
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
import tchecker.util.call_tchecker as call_tchecker

router = APIRouter(prefix="/tck_syntax", tags=["tck_syntax"])

@router.put("/check", summary="Check syntax of a timed automaton")
def check(body: str = Body(...)):

    if not body or body.strip() == "":
        raise HTTPException(status_code=422, detail="Request body cannot be empty")
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(body.encode('utf-8'))
        temp_file_path = temp_file.name
        
    # print(temp_file_path)



    # Call the TChecker syntax check function with following definition:
    # void tck_syntax_check_syntax(const char * output_filename, const char * sysdecl_filename);
    # output_filename is not included in the argtypes as it is set by the call function when has_result=True
    output, result = call_tchecker.call_tchecker_function_in_new_process(
        func_name="tck_syntax_check_syntax",
        argtypes=["ctypes.c_char_p"],
        has_result=True,
        args=[temp_file_path]
    )

    #Cleanup
    os.remove(temp_file_path)

    #remove last newline and trailing spaces
    result = result.strip()

    if result.endswith("Syntax OK"):
        result = {"status": "success", "message": "Syntax is correct"}
    else:
        result = {"status": "error", "message": result}
    return result

@router.put("/to_dot", summary="Convert timed automaton to DOT format")
def to_dot(body: str = Body(...)):

    if not body or body.strip() == "":
        raise HTTPException(status_code=422, detail="Request body cannot be empty")
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(body.encode('utf-8'))
        temp_file_path = temp_file.name
        
    
    # Call the TChecker syntax to DOT conversion function with following definition:
    # void tck_syntax_to_dot(const char * output_filename, const char * sysdecl_filename);
    # output_filename is not included in the argtypes as it is set by the call function when has_result=True
    output, result = call_tchecker.call_tchecker_function_in_new_process(
        func_name="tck_syntax_to_dot",
        argtypes=["ctypes.c_char_p"],
        has_result=True,
        args=[temp_file_path]
    )
    # Cleanup
    os.remove(temp_file_path)
        
    return result

@router.put("/to_json", summary="Convert timed automaton to JSON format")
def to_json(body: str = Body(...)):

    if not body or body.strip() == "":
        raise HTTPException(status_code=422, detail="Request body cannot be empty")
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(body.encode('utf-8'))
        temp_file_path = temp_file.name
        
    
    # Call the TChecker syntax to JSON conversion function with following definition:
    # void tck_syntax_to_json(const char * output_filename, const char * sysdecl_filename);
    # output_filename is not included in the argtypes as it is set by the call function when has_result=True
    output, result = call_tchecker.call_tchecker_function_in_new_process(
        func_name="tck_syntax_to_json",
        argtypes=["ctypes.c_char_p"],
        has_result=True,
        args=[temp_file_path]
    )

    print(output)
    # Cleanup
    os.remove(temp_file_path)
        
    return result


class CreateSynchronizedProductBody(BaseModel):
    sysdecl: str
    process_name: str

@router.put("/create_synchronized_product", summary="Create a synchronized product of timed automata")
def create_product(body: CreateSynchronizedProductBody = Body(...)):

    if not body:
        raise HTTPException(status_code=422, detail="Request body cannot be empty")
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(body.sysdecl.encode('utf-8'))
        temp_file_path = temp_file.name
        
    
    # Call the TChecker create synchronized product function with following definition:
    # void tck_syntax_create_synchronized_product(const char * output_filename, const char * sysdecl_filename, const char * new_system_name);
    # output_filename is not included in the argtypes as it is set by the call function when has_result=True
    output, result = call_tchecker.call_tchecker_function_in_new_process(
        func_name="tck_syntax_create_synchronized_product",
        argtypes=["ctypes.c_char_p", "ctypes.c_char_p"],
        has_result=True,
        args=[temp_file_path, body.process_name]
    )

    # Cleanup
    os.remove(temp_file_path)
        
    return result