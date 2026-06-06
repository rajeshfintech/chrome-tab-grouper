#!/usr/bin/env python3
"""
tabclose — Auto Tab Closer CLI

Commands:
  install               Copy extension to ~/Library/Application Support and guide Chrome setup
  install --profile P   Install for a specific profile (folder name, e.g. "Default")
  remove                Remove installed extension files
  status                Show paths and installation status
  list-profiles         List Chrome profiles on this machine
  config                Open config.json in $EDITOR
  sync                  Push ~/.config/auto-tab-closer/config.json into the installed extension
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR         = Path(__file__).parent.resolve()
EXTENSION_TEMPLATE = SCRIPT_DIR / 'extension'

USER_CONFIG_DIR    = Path.home() / '.config' / 'auto-tab-closer'
USER_CONFIG_JSON   = USER_CONFIG_DIR / 'config.json'

INSTALL_PATH       = Path.home() / 'Library' / 'Application Support' / 'auto-tab-closer'
INSTALLED_EXT      = INSTALL_PATH / 'extension'
INSTALLED_CONFIG   = INSTALLED_EXT / 'config.json'

CHROME_DIR         = Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome'
CHROME_BINARY      = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ok(msg):   print(f'  ✓  {msg}')
def err(msg):  print(f'  ✗  {msg}')
def info(msg): print(f'     {msg}')


def ensure_user_config():
    """Copy the bundled default config.json to ~/.config/auto-tab-closer/ on first run."""
    if USER_CONFIG_JSON.exists():
        return
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(EXTENSION_TEMPLATE / 'config.json', USER_CONFIG_JSON)
    ok(f'Created your config at {USER_CONFIG_JSON}')
    info('Edit it anytime with:  tabclose config')
    print()


def get_profiles():
    profiles = []
    local_state = CHROME_DIR / 'Local State'
    if local_state.exists():
        try:
            state = json.loads(local_state.read_text())
            for folder, pinfo in state.get('profile', {}).get('info_cache', {}).items():
                p = CHROME_DIR / folder
                if p.exists():
                    profiles.append({'folder': folder,
                                     'name': pinfo.get('name', folder),
                                     'path': p})
        except Exception:
            pass
    if not profiles:
        for p in sorted(CHROME_DIR.iterdir()):
            if p.is_dir() and (p.name == 'Default' or p.name.startswith('Profile ')):
                profiles.append({'folder': p.name, 'name': p.name, 'path': p})
    return profiles


def open_chrome_for_profile(folder):
    if Path(CHROME_BINARY).exists():
        subprocess.Popen([CHROME_BINARY, f'--profile-directory={folder}', 'chrome://extensions'])
    else:
        subprocess.run(['open', '-a', 'Google Chrome', 'chrome://extensions'], check=False)


def open_chrome_extensions():
    subprocess.run(['open', '-a', 'Google Chrome', 'chrome://extensions'], check=False)

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_install(args):
    ensure_user_config()

    if INSTALLED_EXT.exists():
        shutil.rmtree(INSTALLED_EXT)
    shutil.copytree(EXTENSION_TEMPLATE, INSTALLED_EXT)
    ok(f'Extension installed at {INSTALLED_EXT}')

    # Use the user's config if it exists, otherwise the bundled default
    shutil.copy(USER_CONFIG_JSON, INSTALLED_CONFIG)
    ok('config.json applied')

    all_profiles = get_profiles()
    if args.profile:
        targets = [p for p in all_profiles
                   if p['folder'] == args.profile or p['name'] == args.profile]
        if not targets:
            err(f"Profile '{args.profile}' not found.")
            cmd_list_profiles(None)
            sys.exit(1)
    else:
        targets = all_profiles

    print(f'\n  Target profile(s): {len(targets)} found')
    print(f"""
  ── One-time setup per profile ───────────────────────────────────────────
    1. Enable  "Developer mode"  (top-right toggle)
    2. Click   "Load unpacked"
    3. Select:  {INSTALLED_EXT}
  Chrome remembers the extension across restarts once loaded.
  ─────────────────────────────────────────────────────────────────────────
""")

    for i, p in enumerate(targets):
        print(f'  [{i+1}/{len(targets)}] Opening Chrome — {p["name"]}  ({p["folder"]})')
        open_chrome_for_profile(p['folder'])
        if i < len(targets) - 1:
            time.sleep(1)


def cmd_remove(_args):
    if INSTALL_PATH.exists():
        shutil.rmtree(INSTALL_PATH)
        ok(f'Removed {INSTALL_PATH}')
    else:
        info('Nothing to remove (not installed).')
    print()
    info('To also remove from Chrome: chrome://extensions → Remove')
    open_chrome_extensions()


def cmd_status(_args):
    print('  Paths:')
    info(f'Extension template  : {EXTENSION_TEMPLATE}')
    info(f'User config         : {USER_CONFIG_JSON}')
    info(f'Installed extension : {INSTALLED_EXT}')
    info(f'Installed config    : {INSTALLED_CONFIG}')
    print()

    if INSTALLED_EXT.exists():
        ok('Extension installed')
    else:
        err('Extension not installed  →  run: tabclose install')

    if USER_CONFIG_JSON.exists():
        mtime = datetime.fromtimestamp(USER_CONFIG_JSON.stat().st_mtime)
        cfg = json.loads(USER_CONFIG_JSON.read_text())
        ok(f'User config last edited: {mtime:%Y-%m-%d %H:%M:%S}')
        info(f'idle_minutes={cfg.get("idle_minutes", "?")}  patterns={len(cfg.get("patterns", []))}')
    else:
        info('No user config yet — will be created on first command')

    if INSTALLED_CONFIG.exists():
        mtime = datetime.fromtimestamp(INSTALLED_CONFIG.stat().st_mtime)
        ok(f'Installed config last synced: {mtime:%Y-%m-%d %H:%M:%S}')
    else:
        err('config.json missing  →  run: tabclose install  or  tabclose sync')

    print()
    cmd_list_profiles(None)


def cmd_list_profiles(_args):
    profiles = get_profiles()
    if not profiles:
        err('No Chrome profiles found')
        return
    print(f'  Chrome profiles  ({CHROME_DIR}):')
    for p in profiles:
        print(f'    {p["folder"]:20}  {p["name"]}')


def cmd_config(_args):
    ensure_user_config()
    editor = os.environ.get('EDITOR', 'nano')
    subprocess.run([editor, str(USER_CONFIG_JSON)])


def cmd_sync(_args):
    ensure_user_config()

    if not INSTALLED_EXT.exists():
        err('Extension not installed yet. Run:  tabclose install')
        sys.exit(1)

    try:
        cfg = json.loads(USER_CONFIG_JSON.read_text())
    except json.JSONDecodeError as e:
        err(f'Invalid JSON in {USER_CONFIG_JSON}: {e}')
        sys.exit(1)

    INSTALLED_CONFIG.write_text(json.dumps(cfg, indent=2))
    ok(f'Synced {USER_CONFIG_JSON}')
    ok(f'     → {INSTALLED_CONFIG}')
    print()
    info(f'idle_minutes : {cfg.get("idle_minutes", "?")}')
    info(f'patterns     : {len(cfg.get("patterns", []))} site(s)')
    print()
    info('The extension picks up config changes within a few seconds.')
    info('Or click "Reload Config" in the extension popup.')

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog='tabclose',
        description='Auto Tab Closer — CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest='cmd', metavar='command')

    p_install = sub.add_parser('install', help='Install extension to Chrome profile(s)')
    p_install.add_argument('--profile', metavar='NAME',
                           help='Profile folder name (e.g. Default, "Profile 2")')

    sub.add_parser('remove',        help='Remove installed extension files')
    sub.add_parser('status',        help='Show paths and installation status')
    sub.add_parser('list-profiles', help='List Chrome profiles')
    sub.add_parser('config',        help='Open config.json in $EDITOR')
    sub.add_parser('sync',          help='Push ~/.config/auto-tab-closer/config.json to installed extension')

    args = parser.parse_args()
    dispatch = {
        'install':       cmd_install,
        'remove':        cmd_remove,
        'status':        cmd_status,
        'list-profiles': cmd_list_profiles,
        'config':        cmd_config,
        'sync':          cmd_sync,
    }
    if args.cmd in dispatch:
        dispatch[args.cmd](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
