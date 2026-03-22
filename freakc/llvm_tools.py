import os
import subprocess
import sys
from pathlib import Path

import llvmlite.binding as llvm


def get_msvc_lib_paths():
    """Attempts to find MSVC and Windows SDK library paths using vswhere and registry."""
    if sys.platform != "win32":
        return []

    # We will try to find paths via vcvarsall.bat if possible, or fall back to clang
    # If the user has Clang installed (which brings LLD), Clang can drive the linking easily.
    return []


def emit_object_file(ir_code: str, out_obj: Path):
    """Parses LLVM IR and emits a native machine code object file."""
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    mod = llvm.parse_assembly(ir_code)
    mod.verify()

    target = llvm.Target.from_default_triple()
    # Optimize for size/speed could be set here
    target_machine = target.create_target_machine(opt=2)

    obj_bytes = target_machine.emit_object(mod)
    out_obj.write_bytes(obj_bytes)
    return out_obj


def link_executable(obj_files: list[Path], out_exe: Path) -> tuple[bool, str]:
    """Links object files into an executable using LLD."""
    # On Windows, lld-link is the LLD driver.
    # To avoid manually resolving the labyrinth of Windows SDK paths,
    # we can invoke clang with -fuse-ld=lld as a linker driver if available.

    # Check if lld-link is in path and if we're in a dev prompt
    in_dev_prompt = "VCToolsInstallDir" in os.environ

    if sys.platform == "win32":
        if in_dev_prompt and shutil.which("lld-link"):
            # We are in a Developer Command Prompt, lld-link can find libs automatically
            cmd = [
                "lld-link",
                f"/out:{out_exe}",
                "/subsystem:console",
                "libucrt.lib",
                "libvcruntime.lib",
                "libcmt.lib",
                "kernel32.lib",
            ] + [str(p) for p in obj_files]
        else:
            # Fall back to using Clang as a linker driver (which uses LLD internally if requested, and finds MSVC paths)
            cmd = (
                ["clang", "-o", str(out_exe)]
                + [str(p) for p in obj_files]
                + ["-fuse-ld=lld", "-g"]
            )
    else:
        # Linux / Mac
        cmd = (
            ["clang", "-o", str(out_exe)]
            + [str(p) for p in obj_files]
            + ["-fuse-ld=lld", "-lm"]
        )

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return False, res.stderr.strip() or res.stdout.strip()
    return True, ""
