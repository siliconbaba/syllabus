#!/usr/bin/env python3
"""Package an existing unsigned Release iPhoneOS .app for SideStore; never edit the source bundle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile


def digest(path):
    with path.open('rb') as stream:
        result = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
        return result.hexdigest()


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f'{args[0]} failed: {result.stdout}{result.stderr}')
    return result.stdout + result.stderr


def inspect_bundle(app, allow_signed_frameworks=False):
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    identifier = info.get('CFBundleIdentifier', '')
    executable = info.get('CFBundleExecutable', '')
    if not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', identifier):
        raise ValueError('Invalid bundle identifier')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', executable) or executable in ('.', '..'):
        raise ValueError('Executable must be an ASCII filename')
    binary = app / executable
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError('Missing executable or execute permission')
    if info.get('CFBundleSupportedPlatforms') != ['iPhoneOS']:
        raise ValueError('Not an iPhoneOS app')
    if info.get('DTPlatformName') != 'iphoneos':
        raise ValueError('Unexpected build platform')
    bundles = [app] + sorted(app.glob('Frameworks/*.framework'))
    for bundle in bundles:
        metadata = plistlib.loads((bundle / 'Info.plist').read_bytes())
        name = metadata['CFBundleExecutable']
        if Path(name).name != name:
            raise ValueError('Unsafe framework executable path')
        exe = bundle / name
        arch = run('/usr/bin/lipo', '-archs', str(exe)).split()
        if 'arm64' not in arch or any(a not in ('arm64', 'arm64e') for a in arch):
            raise ValueError(f'Not device arm64: {bundle.name}: {arch}')
        commands = run('/usr/bin/otool', '-l', str(exe))
        platforms = re.findall(r'\bplatform\s+(\S+)', commands)
        if not platforms or any(p not in ('2', 'IOS') for p in platforms):
            raise ValueError(f'Not iPhoneOS Mach-O: {bundle.name}: {platforms}')
        signing = subprocess.run(['/usr/bin/codesign', '-d', str(bundle)], capture_output=True, text=True)
        if signing.returncode == 0 and bundle != app and allow_signed_frameworks:
            continue
        if signing.returncode == 0 or 'not signed at all' not in signing.stderr:
            raise ValueError('Use an unsigned build (CODE_SIGNING_ALLOWED=NO): ' + str(bundle))
    return info


def clean_copy(source, destination):
    if source.is_symlink():
        raise ValueError('Source app cannot be a symlink')
    destination.mkdir()
    for item in sorted(source.rglob('*')):
        relative = item.relative_to(source)
        if any(part.startswith('._') or part in ('__MACOSX', '.DS_Store') for part in relative.parts):
            continue
        if item.is_symlink():
            raise ValueError('Unsupported symlink: ' + str(relative))
        if '_CodeSignature' in relative.parts and relative.parts[0] == 'Frameworks':
            continue
        if '_CodeSignature' in relative.parts or item.name == 'embedded.mobileprovision':
            raise ValueError('Expected unsigned source without signing resources')
        target = destination / relative
        if item.is_dir():
            target.mkdir(exist_ok=True)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)
            target.chmod(stat.S_IMODE(item.stat().st_mode))
        else:
            raise ValueError('Unsupported file type: ' + str(relative))


def localize_name(app, technical_name):
    path = app / 'Info.plist'
    info = plistlib.loads(path.read_bytes())
    original = info.get('CFBundleDisplayName', info.get('CFBundleName', technical_name))
    info['CFBundleName'] = technical_name
    info['CFBundleDisplayName'] = technical_name
    path.write_bytes(plistlib.dumps(info, fmt=plistlib.FMT_BINARY, sort_keys=False))
    if not original.isascii():
        strings = app / 'ru.lproj' / 'InfoPlist.strings'
        strings.parent.mkdir(exist_ok=True)
        localized = {}
        if strings.exists():
            # Xcode accepts OpenStep .strings as well as XML/binary plists.
            localized = plistlib.loads(subprocess.check_output(['/usr/bin/plutil', '-convert', 'xml1', '-o', '-', str(strings)]))
        localized.setdefault('CFBundleDisplayName', original)
        strings.write_bytes(plistlib.dumps(localized, fmt=plistlib.FMT_BINARY))
    return original


def package(source, output):
    if source.is_symlink():
        raise ValueError('Source app cannot be a symlink')
    if output.is_symlink():
        raise ValueError('Output cannot be a symlink')
    source, output = source.resolve(), output.resolve()
    if source == output or source in output.parents:
        raise ValueError('Output must be outside the source app')
    if output.exists():
        raise ValueError('Refusing to overwrite existing IPA: ' + str(output))
    if source.suffix != '.app' or not source.is_dir():
        raise ValueError('Expected existing Release iPhoneOS .app directory')
    before = inspect_bundle(source, allow_signed_frameworks=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sidestore-') as directory:
        root = Path(directory)
        payload = root / 'Payload'
        payload.mkdir()
        app = payload / 'InteractiveBook.app'
        clean_copy(source, app)
        # Vendor frameworks can retain a signature even in an unsigned Xcode build.
        # Remove it from the staging copy only; SideStore resigns the whole bundle.
        for framework in app.glob('Frameworks/*.framework'):
            signed = subprocess.run(['/usr/bin/codesign', '-d', str(framework)], capture_output=True)
            if signed.returncode == 0:
                run('/usr/bin/codesign', '--remove-signature', str(framework))
        display = localize_name(app, 'InteractiveBook')
        after = inspect_bundle(app)
        if after['CFBundleIdentifier'] != before['CFBundleIdentifier']:
            raise ValueError('Bundle identifier changed')
        files = {str(p.relative_to(root)): digest(p) for p in app.rglob('*') if p.is_file()}
        temporary = root / 'result.ipa'
        with zipfile.ZipFile(temporary, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for item in sorted(payload.rglob('*')):
                archive.write(item, str(item.relative_to(root)))
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP CRC failed')
            names = archive.namelist()
            if len(names) != len(set(names)) or any(not n.startswith('Payload/InteractiveBook.app/') for n in names):
                raise ValueError('Unexpected archive structure')
            extracted = root / 'roundtrip'
            archive.extractall(extracted)
            for entry in archive.infolist():
                (extracted / entry.filename).chmod(stat.S_IMODE(entry.external_attr >> 16))
            restored = {str(p.relative_to(extracted)): digest(p) for p in extracted.rglob('*') if p.is_file()}
            if files != restored:
                raise ValueError('Round-trip changed bundle content')
            inspect_bundle(extracted / 'Payload/InteractiveBook.app')
        # Exclusive creation prevents accidentally replacing a previous release.
        with temporary.open('rb') as src, output.open('xb') as dest:
            try:
                shutil.copyfileobj(src, dest)
            except BaseException:
                output.unlink(missing_ok=True)
                raise
    return {'ipa': str(output), 'sha256': digest(output), 'bytes': output.stat().st_size,
            'bundleIdentifier': before['CFBundleIdentifier'], 'version': before.get('CFBundleShortVersionString'),
            'build': before.get('CFBundleVersion'), 'technicalName': 'InteractiveBook',
            'originalDisplayName': display, 'minimumIOS': before.get('MinimumOSVersion'),
            'signing': 'unsigned; SideStore must resign', 'structure': 'PASS', 'roundtrip': 'PASS',
            'platform': 'iPhoneOS arm64', 'sourceBundleModified': False, 'deviceInstall': 'NOT_TESTED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.app, args.output), ensure_ascii=False, indent=2))
