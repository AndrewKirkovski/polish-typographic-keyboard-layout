"""Compile keyboard layout C source into a Windows DLL using MSVC Build Tools.

Discovers Visual Studio Build Tools and Windows SDK automatically, then
invokes cl.exe, rc.exe, and link.exe with the correct flags for a keyboard
layout DLL (no CRT, no entry point, merged sections).

Usage:
    python compile_kbd.py                # compiles all layouts in build/
    python compile_kbd.py polish         # compile Polish only
    python compile_kbd.py russian        # compile Russian only
    python compile_kbd.py --arch x86     # cross-compile for x86

Prerequisites:
    Visual Studio Build Tools (free) with "Desktop development with C++" workload.
    Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
"""
import subprocess
import struct
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

LAYOUTS = {
    "polish": "pltypo",
    "russian": "rutypo",
}


def find_vswhere():
    """Find vswhere.exe to locate Visual Studio installations."""
    paths = [
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft Visual Studio", "Installer", "vswhere.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft Visual Studio", "Installer", "vswhere.exe"),
    ]
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


def find_msvc(arch="x64"):
    """Find MSVC compiler, linker, and include/lib paths."""
    vswhere = find_vswhere()
    if not vswhere:
        print("ERROR: vswhere.exe not found. Install Visual Studio Build Tools.")
        print("  https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        sys.exit(1)

    # Find VS installation path
    result = subprocess.run(
        [vswhere, "-latest", "-products", "*",
         "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
         "-property", "installationPath"],
        capture_output=True, text=True
    )
    vs_path = result.stdout.strip()
    if not vs_path:
        print("ERROR: No Visual Studio installation with C++ tools found.")
        print("  Install 'Desktop development with C++' workload.")
        sys.exit(1)

    # Find MSVC version
    msvc_dir = os.path.join(vs_path, "VC", "Tools", "MSVC")
    if not os.path.isdir(msvc_dir):
        print(f"ERROR: MSVC tools not found at {msvc_dir}")
        sys.exit(1)
    versions = sorted(os.listdir(msvc_dir))
    msvc_version = versions[-1]

    # Host and target arch mapping
    host = "Hostx64" if os.environ.get("PROCESSOR_ARCHITECTURE") == "AMD64" else "Hostx86"
    target_map = {"x64": "x64", "x86": "x86", "arm64": "arm64"}
    target = target_map.get(arch, "x64")

    bin_dir = os.path.join(msvc_dir, msvc_version, "bin", host, target)
    include_dir = os.path.join(msvc_dir, msvc_version, "include")
    lib_dir = os.path.join(msvc_dir, msvc_version, "lib", target)

    if not os.path.isdir(bin_dir):
        print(f"ERROR: MSVC bin directory not found: {bin_dir}")
        sys.exit(1)

    return {
        "cl": os.path.join(bin_dir, "cl.exe"),
        "link": os.path.join(bin_dir, "link.exe"),
        "include": include_dir,
        "lib": lib_dir,
    }


def find_sdk():
    """Find Windows SDK include and lib paths."""
    sdk_root = os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Windows Kits", "10")
    if not os.path.isdir(sdk_root):
        print(f"ERROR: Windows SDK not found at {sdk_root}")
        sys.exit(1)

    include_base = os.path.join(sdk_root, "Include")
    versions = sorted([d for d in os.listdir(include_base) if d.startswith("10.")])
    if not versions:
        print("ERROR: No Windows SDK versions found.")
        sys.exit(1)
    sdk_version = versions[-1]

    return {
        "um_include": os.path.join(include_base, sdk_version, "um"),
        "shared_include": os.path.join(include_base, sdk_version, "shared"),
        "ucrt_include": os.path.join(include_base, sdk_version, "ucrt"),
        "version": sdk_version,
        "root": sdk_root,
    }


def find_rc(sdk, arch="x64"):
    """Find rc.exe (resource compiler) in the Windows SDK."""
    rc_dir = os.path.join(sdk["root"], "bin", sdk["version"], arch)
    rc_path = os.path.join(rc_dir, "rc.exe")
    if os.path.isfile(rc_path):
        return rc_path
    # Fallback: try x86
    rc_path = os.path.join(sdk["root"], "bin", sdk["version"], "x86", "rc.exe")
    if os.path.isfile(rc_path):
        return rc_path
    print(f"ERROR: rc.exe not found in {rc_dir}")
    sys.exit(1)


def patch_pe(dll_path):
    """Post-link PE patching: fix .data section type and compute checksum.

    Modern MSVC marks merged .data section as CODE (0x20) when .text is merged
    into it. Keyboard layout DLLs need it as INITIALIZED_DATA (0x40) to match
    the standard format (verified against Birman's reference DLLs).
    Also computes a valid PE checksum (required for Native subsystem DLLs).
    """
    with open(dll_path, "rb") as f:
        data = bytearray(f.read())

    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    num_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
    opt_hdr_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
    section_start = pe_offset + 24 + opt_hdr_size

    patched = False
    for i in range(num_sections):
        off = section_start + i * 40
        name = data[off:off + 8].rstrip(b"\x00")
        flags_off = off + 36
        flags = struct.unpack_from("<I", data, flags_off)[0]
        if name == b".data" and (flags & 0x20):
            # Replace CODE (0x20) with INITIALIZED_DATA (0x40)
            new_flags = (flags & ~0x20) | 0x40
            struct.pack_into("<I", data, flags_off, new_flags)
            print(f"  Patched .data section: 0x{flags:08X} -> 0x{new_flags:08X}")
            patched = True

    # Clear DLL characteristics (ASLR/NX/HEVA) — keyboard layout DLLs should have 0
    opt_offset = pe_offset + 24
    magic = struct.unpack_from("<H", data, opt_offset)[0]
    dll_chars_off = opt_offset + (70 if magic == 0x20B else 66)
    old_chars = struct.unpack_from("<H", data, dll_chars_off)[0]
    if old_chars != 0:
        struct.pack_into("<H", data, dll_chars_off, 0)
        print(f"  Cleared DLL characteristics: 0x{old_chars:04X} -> 0x0000")

    # Compute PE checksum (same algorithm as Windows MapFileAndCheckSum)
    checksum_off = pe_offset + 24 + 64  # OptionalHeader + 64 = CheckSum field
    struct.pack_into("<I", data, checksum_off, 0)  # zero out first

    checksum = 0
    for i in range(0, len(data), 2):
        if i == checksum_off or i == checksum_off + 2:
            continue  # skip checksum field itself
        if i + 1 < len(data):
            word = struct.unpack_from("<H", data, i)[0]
        else:
            word = data[i]
        checksum += word
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    checksum = (checksum & 0xFFFF) + (checksum >> 16)
    checksum += len(data)

    struct.pack_into("<I", data, checksum_off, checksum)
    print(f"  PE checksum: 0x{checksum:08X}")

    with open(dll_path, "wb") as f:
        f.write(data)

    if patched:
        print("  PE patching complete.")


def compile_layout(name, arch="x64"):
    """Compile a keyboard layout from build/<name>.c to dist/<name>.dll."""
    build_dir = os.path.join(SCRIPT_DIR, "build")
    dist_dir = os.path.join(SCRIPT_DIR, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    c_file = os.path.join(build_dir, f"{name}.c")
    rc_file = os.path.join(build_dir, f"{name}.rc")
    def_file = os.path.join(build_dir, f"{name}.def")

    for f in [c_file, rc_file, def_file]:
        if not os.path.isfile(f):
            print(f"ERROR: {f} not found. Run build_kbd_c.py first.")
            sys.exit(1)

    obj_file = os.path.join(build_dir, f"{name}.obj")
    res_file = os.path.join(build_dir, f"{name}.res")
    dll_file = os.path.join(dist_dir, f"{name}.dll")

    # Find tools
    msvc = find_msvc(arch)
    sdk = find_sdk()
    rc_exe = find_rc(sdk, arch)

    print(f"  MSVC: {msvc['cl']}")
    print(f"  SDK:  {sdk['version']}")
    print(f"  RC:   {rc_exe}")

    # ── Step 1: Compile C → OBJ ────────────────────────────────────────
    print(f"  Compiling {name}.c ...")
    cl_cmd_str = " ".join([
        f'"{msvc["cl"]}"',
        "/nologo /c /O1 /W3 /GS- /Zl /utf-8",
        "/DUNICODE /D_UNICODE /D_USRDLL",
        "/DNTDDI_VERSION=0x06010000",
        f'/I"{msvc["include"]}"',
        f'/I"{sdk["um_include"]}"',
        f'/I"{sdk["shared_include"]}"',
        f'/I"{sdk["ucrt_include"]}"',
        f'/Fo"{obj_file}"',
        f'"{c_file}"',
    ])

    result = subprocess.run(cl_cmd_str, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  COMPILE FAILED:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)
    if result.stderr:
        # cl.exe outputs to stderr even on success
        for line in result.stderr.strip().split("\n"):
            if line.strip():
                print(f"    {line.strip()}")

    # ── Step 2: Compile RC → RES ───────────────────────────────────────
    print(f"  Compiling {name}.rc ...")
    rc_cmd = f'"{rc_exe}" /nologo /I"{msvc["include"]}" /I"{sdk["um_include"]}" /I"{sdk["shared_include"]}" /I"{sdk["ucrt_include"]}" /fo"{res_file}" "{rc_file}"'
    result = subprocess.run(rc_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  RC FAILED:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)

    # ── Step 3: Link OBJ + RES → DLL ──────────────────────────────────
    print(f"  Linking {name}.dll ...")
    link_cmd = " ".join([
        f'"{msvc["link"]}"',
        "/nologo /dll /noentry",
        f'/def:"{def_file}"',
        "/subsystem:native,5.02",
        "/merge:.rdata=.data /merge:.bss=.data /merge:.text=.data",
        "/section:.data,re /section:.rsrc,dr",
        "/DYNAMICBASE:NO /NXCOMPAT:NO",
        "/ignore:4254",
        f'/out:"{dll_file}"',
        f'"{obj_file}" "{res_file}"',
    ])

    result = subprocess.run(link_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  LINK FAILED:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)

    # Check output
    if os.path.isfile(dll_file):
        size = os.path.getsize(dll_file)
        print(f"  -> {dll_file} ({size:,} bytes)")
    else:
        print(f"  ERROR: {dll_file} was not created.")
        sys.exit(1)

    # ── Step 4: Post-link PE patching ─────────────────────────────────
    patch_pe(dll_file)

    # Clean intermediate files
    for f in [obj_file, res_file]:
        if os.path.isfile(f):
            os.remove(f)

    # Also clean .exp and .lib (linker byproducts)
    for ext in [".exp", ".lib"]:
        byproduct = os.path.join(dist_dir, f"{name}{ext}")
        if os.path.isfile(byproduct):
            os.remove(byproduct)


def main():
    arch = "x64"
    targets = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--arch" and i + 1 < len(args):
            arch = args[i + 1]
            if arch not in ("x64", "x86", "arm64"):
                print(f"Invalid arch: {arch}. Use x64, x86, or arm64.")
                sys.exit(1)
            i += 2
            continue
        elif arg.startswith("--arch="):
            arch = arg.split("=", 1)[1]
            if arch not in ("x64", "x86", "arm64"):
                print(f"Invalid arch: {arch}. Use x64, x86, or arm64.")
                sys.exit(1)
        elif arg in LAYOUTS:
            targets.append(arg)
        else:
            print(f"Unknown argument: {arg}")
            print(f"Usage: python compile_kbd.py [polish|russian] [--arch x64|x86|arm64]")
            sys.exit(1)
        i += 1

    if not targets:
        # Compile all layouts that have generated C files
        for target, name in LAYOUTS.items():
            if os.path.isfile(os.path.join(SCRIPT_DIR, "build", f"{name}.c")):
                targets.append(target)

    if not targets:
        print("No C source files found. Run build_kbd_c.py first.")
        sys.exit(1)

    for target in targets:
        name = LAYOUTS[target]
        print(f"Compiling {target} ({name}) for {arch}...")
        compile_layout(name, arch)

    print("Done.")


if __name__ == "__main__":
    main()
