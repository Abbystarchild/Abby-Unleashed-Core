"""Conservative path authorization precheck, not a race-free filesystem sandbox."""
import os
import stat


def _canonical_without_links(value, *, allow_missing):
    if not isinstance(value, str) or not value or '\x00' in value:
        raise ValueError('Invalid path')
    if not os.path.isabs(value):
        raise ValueError('Absolute paths required')
    if os.name == 'nt':
        drive, tail = os.path.splitdrive(value)
        if len(drive) != 2 or drive[1] != ':' or ':' in tail:
            raise ValueError('Only local drive paths without alternate streams')
        parts = value.replace('\\', '/').split('/')
    else:
        parts = value.split('/')
    if '..' in parts:
        raise ValueError('Parent traversal is not accepted')
    target = os.path.abspath(value)
    cursor = target
    missing = []
    existing = None
    while True:
        try:
            info = os.lstat(cursor)
        except FileNotFoundError:
            if not allow_missing or existing is not None:
                raise
            missing.append(os.path.basename(cursor))
        else:
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Symlinks and Windows reparse points are not accepted')
            if existing is None:
                existing = cursor
                if missing and not stat.S_ISDIR(info.st_mode):
                    raise ValueError('Missing path must descend from a directory')
        parent = os.path.dirname(cursor)
        if parent == cursor:
            break
        cursor = parent
    if existing is None:
        raise ValueError('No existing ancestor')
    # Resolve only after inspecting every existing ancestor. strict=True fails closed
    # on resolution errors. Missing suffixes support writes to new child paths.
    resolved = os.path.realpath(existing, strict=True)
    return os.path.join(resolved, *reversed(missing)) if missing else resolved


def is_within_workspaces(filepath, workspaces):
    try:
        candidate = _canonical_without_links(filepath, allow_missing=True)
    except (OSError, ValueError, TypeError):
        return False
    for workspace in workspaces:
        try:
            root = _canonical_without_links(workspace, allow_missing=False)
            if not os.path.isdir(root):
                continue
            # Compare canonical spellings, without blindly case-folding distinct
            # entries on Windows directories configured as case-sensitive.
            if os.path.commonpath((candidate, root)) == root:
                return True
        except (OSError, ValueError, TypeError):
            continue
    return False
