#!/usr/bin/python3 -I
"""Reversible, fail-closed Matrix palette overlay for orca-ide-bin; stdlib only."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import struct
import sys
import tempfile
from pathlib import Path

ARCHIVE = Path('/usr/lib/orca-ide/app.asar')
STATE = Path('/var/lib/orca-matrix-theme')
COLOR_REPLACEMENTS = (('--background:#0a0a0a', '--background:#020906'), ('--editor-surface:#1e1e1e', '--editor-surface:#010503'), ('--foreground:#fafafa', '--foreground:#b6ffc1'), ('--card:#171717', '--card:#06120a'), ('--card-foreground:#fafafa', '--card-foreground:#aaffb6'), ('--popover:#171717', '--popover:#07160b'), ('--popover-foreground:#fafafa', '--popover-foreground:#b6ffc1'), ('--primary:#e5e5e5', '--primary:#25f35d'), ('--primary-foreground:#171717', '--primary-foreground:#001b07'), ('--secondary:#262626', '--secondary:#0c2412'), ('--secondary-foreground:#fafafa', '--secondary-foreground:#7ce790'), ('--muted:#262626', '--muted:#0b1c0f'), ('--muted-foreground:#a1a1a1', '--muted-foreground:#65c87a'), ('--accent:#404040', '--accent:#13351a'), ('--accent-foreground:#fafafa', '--accent-foreground:#b6ffc1'), ('--border:#ffffff12', '--border:#174a2480'), ('--input:#ffffff26', '--input:#1d4b2990'), ('--ring:#737373', '--ring:#25f35d'), ('--workspace-status-done:#c7a594', '--workspace-status-done:#65c87a'), ('--workspace-status-progress:#d4a300', '--workspace-status-progress:#25f35d'), ('--worktree-sidebar:#2a2a2a', '--worktree-sidebar:#030d06'), ('--worktree-sidebar-foreground:#fafafa', '--worktree-sidebar-foreground:#8cec9f'), ('--worktree-sidebar-accent:#353535', '--worktree-sidebar-accent:#0e2b15'), ('--worktree-sidebar-accent-foreground:#fafafa', '--worktree-sidebar-accent-foreground:#afffbb'), ('--worktree-sidebar-border:#ffffff12', '--worktree-sidebar-border:#174a2480'), ('--worktree-sidebar-ring:#737373', '--worktree-sidebar-ring:#25f35d'), ('--sidebar:#171717', '--sidebar:#030d06'), ('--sidebar-foreground:#fafafa', '--sidebar-foreground:#8cec9f'), ('--sidebar-primary:#1447e6', '--sidebar-primary:#25f35d'), ('--sidebar-primary-foreground:#fafafa', '--sidebar-primary-foreground:#001b07'), ('--sidebar-accent:#262626', '--sidebar-accent:#0e2b15'), ('--sidebar-accent-foreground:#fafafa', '--sidebar-accent-foreground:#afffbb'), ('--sidebar-border:#ffffff12', '--sidebar-border:#174a2480'), ('--sidebar-ring:#525252', '--sidebar-ring:#25f35d'), ('--status-success:#86efac', '--status-success:#25f35d'), ('--terminal-pane-title-on-dark-fg:#ffffff85', '--terminal-pane-title-on-dark-fg:#65c87a9c'), ('--terminal-pane-title-on-dark-input-fg:#ffffffb3', '--terminal-pane-title-on-dark-input-fg:#78ed8ecc'), ('--terminal-pane-title-on-dark-placeholder:#ffffff61', '--terminal-pane-title-on-dark-placeholder:#65c87a8f'), ('--terminal-pane-title-on-dark-button-fg:#fff', '--terminal-pane-title-on-dark-button-fg:#7e8'), ('--terminal-pane-title-on-dark-button-hover-fg:#fff', '--terminal-pane-title-on-dark-button-hover-fg:#7e8'), ('--terminal-pane-title-on-dark-input-bg:#ffffff0a', '--terminal-pane-title-on-dark-input-bg:#0f3e1a55'), ('--terminal-pane-title-on-dark-separator:#ffffff0f', '--terminal-pane-title-on-dark-separator:#1d6b2b77'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse(data):
    require(len(data) >= 16, 'Truncated ASAR')
    size_payload, header_size, header_payload, json_size = struct.unpack_from('<4I', data)
    require(size_payload == 4 and header_payload + 4 == header_size,
            'Unsupported ASAR pickle structure')
    require(header_payload == (4 + json_size + 3) // 4 * 4,
            'Unsupported ASAR header padding')
    start = 8 + header_size  # Includes pickle framing and alignment padding.
    require(16 + json_size <= start <= len(data), 'Invalid ASAR header bounds')
    manifest = json.loads(data[16:16 + json_size])
    require(isinstance(manifest.get('files'), dict), 'Missing ASAR file tree')
    return manifest, start, json_size


def entries(tree, prefix=''):
    for name, entry in tree.items():
        path = prefix + name
        if 'files' in entry:
            yield from entries(entry['files'], path + '/')
        else:
            yield path, entry


def asset_bytes(data, start, entry):
    require(not entry.get('unpacked') and 'link' not in entry,
            'Theme CSS must be packed, not a link')
    require(isinstance(entry.get('offset'), str) and entry['offset'].isdigit(),
            'Invalid asset offset')
    size = entry.get('size')
    require(type(size) is int and size >= 0, 'Invalid asset size')
    offset = start + int(entry['offset'])
    require(start <= offset <= offset + size <= len(data), 'Invalid asset bounds')
    return offset, bytes(data[offset:offset + size])


def integrity_for(content, existing):
    require(isinstance(existing, dict) and existing.get('algorithm') == 'SHA256',
            'Unsupported asset integrity metadata')
    block_size = existing.get('blockSize')
    require(type(block_size) is int and block_size > 0, 'Invalid integrity block size')
    result = dict(existing)
    result['hash'] = digest(content)
    result['blocks'] = [digest(content[i:i + block_size])
                        for i in range(0, len(content), block_size)]
    return result


def verify_integrity(content, entry, name):
    require(entry.get('integrity') == integrity_for(content, entry.get('integrity')),
            f'{name}: integrity mismatch; archive left unchanged')


def transform(data):
    manifest, start, json_size = parse(data)
    output = bytearray(data)
    found = {'out/renderer/assets/': [], 'out/web/assets/': []}
    updates = []
    spans = []
    for name, entry in entries(manifest['files']):
        tree = next((prefix for prefix in found if name.startswith(prefix)), None)
        if not tree or not name.endswith('.css'):
            continue
        offset, css = asset_bytes(data, start, entry)
        # Discover the palette by variables, independent of Vite filename hashes.
        if not all(token in css for token in
                   (b'--background:', b'--editor-surface:', b'--sidebar-primary:')):
            continue
        found[tree].append(name)
        verify_integrity(css, entry, name)
        for old, new in COLOR_REPLACEMENTS:
            old, new = old.encode(), new.encode()
            require(len(old) == len(new), 'Palette substitution changes length')
            variable, old_color = old.split(b':', 1)
            new_color = new.split(b':', 1)[1]
            pattern = re.compile(rb'(?<![\w-])' + re.escape(variable) + rb':([^;}]+)(?=[;}])')
            values = pattern.findall(css)
            require(any(value in (old_color, new_color) for value in values),
                    f'{name}: missing or changed variable {variable.decode()}; unsupported Orca palette')
            css = pattern.sub(lambda match: variable + b':' + (new_color if match[1] == old_color else match[1]), css)
        require(len(css) == entry['size'], f'{name}: CSS size changed')
        spans.append((offset, offset + len(css)))
        output[offset:offset + len(css)] = css
        entry['integrity'] = integrity_for(css, entry['integrity'])
        updates.append(name)
    require(all(len(names) == 1 for names in found.values()),
            f'Expected one palette stylesheet per renderer/web tree, found {found}')
    spans.sort()
    require(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'Overlapping CSS assets')
    # Preserve every original header byte except fixed-width integrity digests.
    # JSON reserialization can change escaping/spacing and archive offsets.
    original_manifest, _, _ = parse(data)
    header = bytes(data[16:16 + json_size])
    old_entries = dict(entries(original_manifest['files']))
    new_entries = dict(entries(manifest['files']))
    replacements = {}
    for name in updates:
        old = old_entries[name]['integrity']
        new = new_entries[name]['integrity']
        for before, after in zip([old['hash'], *old['blocks']], [new['hash'], *new['blocks']], strict=True):
            if before != after:
                require(re.fullmatch('[0-9a-f]{64}', before) is not None, 'Invalid SHA256 digest')
                require(before not in replacements or replacements[before] == after,
                        'Ambiguous shared integrity digest')
                replacements[before] = after
    # Replace only digest string values; compare the entire parsed manifest below
    # to ensure no unrelated entry was modified by a shared digest.
    for before, after in replacements.items():
        header = header.replace(('"' + before + '"').encode(), ('"' + after + '"').encode())
    require(json.loads(header) == manifest, 'Header digest replacement affected another asset')
    output[16:16 + json_size] = header
    result = bytes(output)
    parsed, final_start, _ = parse(result)
    require(final_start == start and len(result) == len(data), 'ASAR layout changed')
    for name, entry in entries(parsed['files']):
        if name in updates:
            _, content = asset_bytes(result, final_start, entry)
            verify_integrity(content, entry, name)
    return result, updates


def legacy_output(data):
    """Reproduce the old script exactly, solely to authorize recovery."""
    manifest, _, json_size = parse(data)
    output = bytearray(data)
    for name in ('out/renderer/assets/I18nProvider-BYZ_5f-z.css',
                 'out/web/assets/I18nProvider-BYZ_5f-z.css'):
        entry = dict(entries(manifest['files']))[name]
        offset, css = asset_bytes(data, 16 + json_size, entry)
        for old, new in COLOR_REPLACEMENTS:
            require(old.encode() in css, 'Legacy backup does not match original palette')
            css = css.replace(old.encode(), new.encode())
        output[offset:offset + len(css)] = css
        entry['integrity'] = integrity_for(css, entry['integrity'])
    header = json.dumps(manifest, separators=(',', ':'), ensure_ascii=False).encode()
    require(len(header) == json_size, 'Legacy header size mismatch')
    output[16:16 + json_size] = header
    return bytes(output)


def safe_path(path, directory=False):
    # Check every parent as well as the leaf: no symlinks or writable root paths.
    for item in [*reversed(path.parents), path]:
        st = item.lstat()
        require(not stat.S_ISLNK(st.st_mode), f'Symlink refused: {item}')
        require(st.st_uid == 0 and not st.st_mode & 0o022, f'Unsafe ownership/mode: {item}')
    st = path.stat()
    require(stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode),
            f'Unexpected file type: {path}')


def atomic_write(path, content, metadata):
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fchmod(stream.fileno(), stat.S_IMODE(metadata.st_mode))
            os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
            os.fsync(stream.fileno())
        require(temp.read_bytes() == content, 'Staged file verification failed')
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='Read only compatibility and integrity check')
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--repair-legacy', action='store_true', help='Recover only an exact old-script output from the root-owned legacy-original.asar')
    mode.add_argument('--restore', action='store_true', help='Restore only the recorded matching archive')
    args = parser.parse_args()
    if args.check:
        data = ARCHIVE.read_bytes()
        patched, assets = transform(data)
        print(json.dumps({'status': 'already-patched' if patched == data else 'compatible',
                          'archive_sha256': digest(data), 'assets': assets}, indent=2))
        return
    require(os.geteuid() == 0, 'Apply/restore require root; check works without root')
    safe_path(ARCHIVE)
    safe_path(STATE, directory=True)
    lock = STATE / 'lock'
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        safe_path(lock)
        metadata = ARCHIVE.stat()
        original = ARCHIVE.read_bytes()
        record = STATE / 'last-apply.json'
        if args.restore:
            safe_path(record)
            receipt = json.loads(record.read_text())
            require(digest(original) == receipt['patched_sha256'],
                    'Archive changed since patching; refusing to restore over another Orca version')
            backup = STATE / (receipt['original_sha256'] + '.asar')
            safe_path(backup)
            restored = backup.read_bytes()
            require(digest(restored) == receipt['original_sha256'], 'Backup checksum mismatch')
            parse(restored)
            atomic_write(ARCHIVE, restored, metadata)
            require(ARCHIVE.read_bytes() == restored, 'Restore verification failed')
            print(f'Restored {backup}; disable the hook to keep the original palette.')
            return
        baseline = original
        if args.repair_legacy:
            legacy = STATE / 'legacy-original.asar'
            safe_path(legacy)
            baseline = legacy.read_bytes()
            require(legacy_output(baseline) == original, 'Legacy backup does not reproduce installed archive; refusing recovery')
            damaged = STATE / (digest(original) + '.legacy-damaged.asar')
            if damaged.exists() or damaged.is_symlink():
                safe_path(damaged)
                require(damaged.read_bytes() == original, 'Damaged archive backup mismatch')
            else:
                atomic_write(damaged, original, metadata)
        patched, assets = transform(baseline)
        if patched == original:
            print('Matrix palette and CSS integrity verified; already patched, no changes.')
            return
        backup = STATE / (digest(baseline) + '.asar')
        if backup.exists() or backup.is_symlink():
            safe_path(backup)
            require(backup.read_bytes() == baseline, 'Existing backup checksum mismatch')
        else:
            atomic_write(backup, baseline, metadata)
        receipt = {'original_sha256': digest(baseline), 'patched_sha256': digest(patched),
                   'backup': str(backup), 'assets': assets}
        # Save restoration metadata before replacing the archive.
        if record.exists() or record.is_symlink():
            safe_path(record)
        atomic_write(record, (json.dumps(receipt, indent=2) + '\n').encode(), metadata)
        require(ARCHIVE.read_bytes() == original, 'Archive changed during patch preparation')
        try:
            atomic_write(ARCHIVE, patched, metadata)
            installed = ARCHIVE.read_bytes()
            require(installed == patched, 'Installed archive checksum mismatch')
            verified, _ = transform(installed)
            require(verified == installed, 'Installed palette verification failed')
        except Exception:
            atomic_write(ARCHIVE, original, metadata)
            require(ARCHIVE.read_bytes() == original, 'Rollback verification failed')
            raise
        print(json.dumps({'status': 'patched-and-verified', **receipt}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'orca-matrix-theme: {exc}', file=sys.stderr)
        sys.exit(1)
