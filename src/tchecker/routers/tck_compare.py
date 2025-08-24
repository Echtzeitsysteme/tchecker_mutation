import ctypes
import tempfile
import os
from typing import Optional
from fastapi import APIRouter, Body
from pydantic import BaseModel
import util.call_tchecker as call_tchecker
import asyncio

router = APIRouter(prefix="/tck_compare", tags=["tck_compare"])


class TckCompareBody(BaseModel):
    first_sysdecl: str
    second_sysdecl: str
    relationship: int
    block_size: Optional[int] = None
    table_size: Optional[int] = None

@router.put("")
async def compare(body: TckCompareBody = Body(...)):
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file_first_sysdecl:
        temp_file_first_sysdecl.write(body.first_sysdecl.encode('utf-8'))
        temp_file_path_first_sysdecl = temp_file_first_sysdecl.name
    with tempfile.NamedTemporaryFile(delete=False) as temp_file_second_sysdecl:
        temp_file_second_sysdecl.write(body.second_sysdecl.encode('utf-8'))
        temp_file_path_second_sysdecl  = temp_file_second_sysdecl.name
        
    
    # Call the TChecker compare function with following definition:
    # void tck_compare(const char * output_filename, const char * first_sysdecl_filename, const char * second_sysdecl_filename,
    #              tck_compare_relationship_t relationship, int * block_size, int * table_size);
    # output_filename is not included in the argtypes as it is set by the call function when has_result=True
    output, result = call_tchecker.call_tchecker_function_in_new_process(
        func_name="tck_compare",
        argtypes=["ctypes.c_char_p", "ctypes.c_char_p", "ctypes.c_int", "ctypes.POINTER(ctypes.c_int)", "ctypes.POINTER(ctypes.c_int)"],
        has_result=True,
        args=[temp_file_path_first_sysdecl, temp_file_path_second_sysdecl, body.relationship, body.block_size, body.table_size]
    )

    # Cleanup
    os.remove(temp_file_path_first_sysdecl)
    os.remove(temp_file_path_second_sysdecl)

    resultMap = {
        "stats": output,
    }
    print("Output: " + output)
    
    return resultMap