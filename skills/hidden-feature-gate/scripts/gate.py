#!/usr/bin/env python3
"""App Review 2.5.19 gate: find hidden switches in release source or a built binary.
Exit 0 = PASS, 1 = FAIL (hits found), 2 = usage error. Read-only."""
import argparse, os, plistlib, re, subprocess, sys

SOURCE_SWITCH = re.compile(r'ProcessInfo\.processInfo\.(arguments|environment)|UserDefaults\.standard\.(bool|string|object)\(forKey:\s*"[^"]*(debug|demo|mock|unlock|screenshot|hidden|secret)[^"]*"', re.I)
SOURCE_WORD = re.compile(r'\b\w*(Demo|Mock|Unlock(?:ed)?|Screenshots?Mode|DebugMenu|HiddenFeature|SecretMenu)(?![a-z])\w*\b')
SKIP_DIRS = ('/.build/', '/Tests/', 'Tests/', '/UITests/', '/Preview Content/', '/build/', '/DerivedData/')
BINARY_PATTERNS = [
    re.compile(r'^-{1,2}[A-Za-z][A-Za-z0-9]*(Demo|demo|Mock|mock|Screenshot|screenshot|Auto[A-Z][a-z]+|offline-[a-z-]+)[A-Za-z0-9-]*$'),
    re.compile(r'(Unlocked?Mock|MockPurchase|debugMenu|DebugMenu|hiddenFeature|secretMenu|screenshots?-?mode)', re.I),
    re.compile(r'^(https?://)?(localhost|127\.0\.0\.1)(:\d+)?(/|$)'),
    re.compile(r'^-{1,2}(open|skip|force|seed|enable|disable|bypass|fake|stub)[A-Z][A-Za-z0-9]+$'),
]

def scan_source(root):
    hits = []
    for dirpath, _, files in os.walk(root):
        rel = dirpath + '/'
        if any(s in rel for s in SKIP_DIRS):
            continue
        for f in files:
            if not f.endswith('.swift'):
                continue
            path = os.path.join(dirpath, f)
            stack = []
            for n, line in enumerate(open(path, errors='ignore'), 1):
                s = line.strip()
                if s.startswith('#if'):
                    stack.append('DEBUG' in s or 'targetEnvironment(simulator)' in s)
                    continue
                if s.startswith('#elseif') and stack:
                    stack[-1] = 'DEBUG' in s
                    continue
                if s.startswith('#else') and stack:
                    stack[-1] = not stack[-1]
                    continue
                if s.startswith('#endif') and stack:
                    stack.pop()
                    continue
                if any(stack) or s.startswith('//'):
                    continue
                if SOURCE_SWITCH.search(line):
                    hits.append(f'{path}:{n}: switch outside #if DEBUG: {s[:140]}')
                elif SOURCE_WORD.search(line) and ('"' in line or 'case ' in s or 'func ' in s or 'var ' in s or 'let ' in s):
                    hits.append(f'{path}:{n}: demo/mock/unlock identifier outside #if DEBUG: {s[:140]}')
    return hits

def find_executable(path):
    if path.endswith('.xcarchive'):
        apps = os.path.join(path, 'Products', 'Applications')
        names = [n for n in os.listdir(apps) if n.endswith('.app')] if os.path.isdir(apps) else []
        if not names:
            sys.exit(f'No .app inside {apps}')
        path = os.path.join(apps, names[0])
    if path.endswith('.app'):
        info = os.path.join(path, 'Info.plist')
        if not os.path.exists(info):
            info = os.path.join(path, 'Contents', 'Info.plist')
        with open(info, 'rb') as fh:
            exe = plistlib.load(fh)['CFBundleExecutable']
        for candidate in (os.path.join(path, exe), os.path.join(path, 'Contents', 'MacOS', exe)):
            if os.path.exists(candidate):
                return candidate
        sys.exit(f'Executable {exe} not found in {path}')
    return path

MACHO_MAGIC = {b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xfe\xed\xfa\xcf'}

def machos_in_bundle(exe):
    """The main executable plus every Mach-O inside the bundle (debug dylibs, frameworks, extensions)."""
    bundle = exe
    while bundle != '/' and not bundle.endswith(('.app', '.xcarchive')):
        bundle = os.path.dirname(bundle)
    found = [exe]
    if bundle.endswith('.app'):
        for dirpath, _, files in os.walk(bundle):
            for f in files:
                p = os.path.join(dirpath, f)
                if p == exe or os.path.islink(p):
                    continue
                try:
                    with open(p, 'rb') as fh:
                        if fh.read(4) in MACHO_MAGIC:
                            found.append(p)
                except OSError:
                    pass
    return found

def scan_binary(path):
    exe = find_executable(path)
    hits = set()
    files = machos_in_bundle(exe)
    for f in files:
        out = subprocess.run(['strings', '-a', f], capture_output=True, text=True, errors='ignore').stdout.splitlines()
        for s in (x.strip() for x in out):
            if 3 <= len(s) <= 120 and any(p.search(s) for p in BINARY_PATTERNS):
                hits.add(f'{os.path.basename(f)}: {s}')
    return f'{exe} (+{len(files) - 1} more Mach-O files)', [f'string in binary: {h}' for h in sorted(hits)]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', action='append', default=[], help='app source folder (repeatable)')
    ap.add_argument('--binary', help='.xcarchive, .app or executable to scan with strings')
    a = ap.parse_args()
    if not a.source and not a.binary:
        ap.print_usage(); sys.exit(2)
    hits = []
    for root in a.source:
        hits += scan_source(root)
    if a.binary:
        exe, bhits = scan_binary(a.binary)
        print(f'binary: {exe}')
        hits += bhits
    for h in hits:
        print(h)
    print(f'\n{"FAIL" if hits else "PASS"}: {len(hits)} hit(s). App Review 2.5.19: explain or remove every hit before upload.')
    sys.exit(1 if hits else 0)

if __name__ == '__main__':
    main()
