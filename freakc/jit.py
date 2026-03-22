import ctypes
import os
import subprocess
import sys
from pathlib import Path

import llvmlite.binding as llvm


def ensure_runtime_dll(runtime_dir: Path) -> Path:
    """Compiles the C runtime into a DLL for the JIT to use."""
    dll_path = runtime_dir / "freak_runtime.dll"
    c_path = runtime_dir / "freak_runtime.c"

    # We use Clang to compile the runtime into a shared library just once
    cmd = [
        "clang",
        "-shared",
        "-o",
        str(dll_path),
        str(c_path),
        f"-I{runtime_dir}",
        "-O2",
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return dll_path


def run_jit(ir_code: str, runtime_dir: Path):
    """Executes LLVM IR code directly in memory."""
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    # 1. Compile and load the C runtime DLL
    dll_path = ensure_runtime_dll(runtime_dir)

    # On Windows, we load the DLL to make its symbols available to the process
    # llvmlite uses the current process's symbol table to resolve external C calls
    ctypes.CDLL(str(dll_path), mode=os.RTLD_GLOBAL if hasattr(os, "RTLD_GLOBAL") else 0)
    # Also load the MSVCRT for standard C library functions (puts, printf, etc)
    if sys.platform == "win32":
        ctypes.cdll.msvcrt

    # Bind external symbols explicitly for LLVMLite just in case
    dll = ctypes.CDLL(str(dll_path))

    # Extract external function names from IR and map them
    # This is a bit of a hack, normally we'd load the symbols directly
    for sym in [
        "freak_llvm_word_from_int",
        "freak_llvm_word_from_bool",
        "freak_llvm_word_concat",
        "freak_llvm_word_eq",
        "freak_llvm_word_neq",
        "freak_llvm_word_length",
        "freak_llvm_word_char_at",
        "freak_llvm_word_contains",
        "freak_llvm_word_starts_with",
        "freak_llvm_word_ends_with",
        "freak_llvm_word_to_upper",
        "freak_llvm_word_to_lower",
        "freak_llvm_word_trim",
        "freak_llvm_word_replace",
        "freak_llvm_word_to_int",
        "freak_llvm_say",
        "freak_llvm_print_str",
        "freak_llvm_print_int",
        "freak_llvm_print_newline",
        "freak_llvm_ask",
        "freak_llvm_fs_read",
        "freak_llvm_fs_write",
        "freak_llvm_process_args_count",
        "freak_llvm_process_arg",
        "freak_llvm_process_exit",
        "freak_llvm_setup_args",
    ]:
        try:
            addr = ctypes.cast(getattr(dll, sym), ctypes.c_void_p).value
            llvm.add_symbol(sym, addr)
        except AttributeError:
            pass  # Symbol not found or needed

    try:
        # Resolve C library symbols that Windows might hide
        msvcrt = ctypes.cdll.msvcrt
        llvm.add_symbol("puts", ctypes.cast(msvcrt.puts, ctypes.c_void_p).value)
        llvm.add_symbol("printf", ctypes.cast(msvcrt.printf, ctypes.c_void_p).value)
    except:
        pass

    # 2. Parse the LLVM IR
    mod = llvm.parse_assembly(ir_code)
    mod.verify()

    # 3. Create Execution Engine (JIT)
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()

    # Compile the module to machine code
    engine = llvm.create_mcjit_compiler(mod, target_machine)
    engine.finalize_object()
    engine.run_static_constructors()

    # 4. Grab the main function and execute
    func_ptr = engine.get_function_address("main")

    # Create a ctypes function matching: int main(int argc, char** argv)
    cfunc = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)
    )(func_ptr)

    # Call it!
    res = cfunc(0, None)
    return res
