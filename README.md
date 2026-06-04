# Tab Auto Grouper

A Chrome extension that automatically groups tabs by URL rules, with a CLI for managing config and installation.

## Install via Homebrew

```bash
brew tap rajeshfintech/tools
brew install tab-auto-grouper
tabgroups install
```

`tabgroups install` copies the extension to `~/Library/Application Support/chrome-tab-grouper/extension` and guides you through the one-time Chrome setup.

---

## Manual install (without Homebrew)

```bash
git clone https://github.com/rajeshfintech/chrome-tab-grouper.git
pip install pyyaml
# Add to PATH
export PATH="$PATH:$(pwd)/chrome-tab-grouper/bin"
tabgroups install
```

---

## One-time Chrome setup (per profile)

After `tabgroups install`, do this once for each Chrome profile:

1. Open Chrome with that profile active
2. Go to `chrome://extensions`
3. Enable **Developer mode** (toggle, top-right)
4. Click **Load unpacked** → select `~/Library/Application Support/chrome-tab-grouper/extension`

Chrome remembers the extension across restarts. After a `brew upgrade`, click the **↺ reload** icon on the extension card in `chrome://extensions`.

---

## CLI reference

| Command | Description |
|---|---|
| `tabgroups install` | Copy extension and guide Chrome setup for all profiles |
| `tabgroups install --profile "Profile 2"` | Install for a specific profile only |
| `tabgroups sync` | Apply config changes to the running extension |
| `tabgroups config` | Open `config.yaml` in `$EDITOR` |
| `tabgroups remove` | Remove the installed extension files |
| `tabgroups list-profiles` | List Chrome profiles on this machine |
| `tabgroups status` | Show paths and installation status |

---

## Configuration

Your config lives at `~/.config/tab-auto-grouper/config.yaml`. It is created automatically on first run and is **never modified by `brew upgrade` or `brew reinstall`**.

Edit it with:

```bash
tabgroups config   # opens in $EDITOR
tabgroups sync     # apply changes — extension picks them up within 5 s
```

### Config format

```yaml
version: 1

# Tabs matching any rule here are never grouped (e.g. bookmarks bar links)
exclude:
  - domain: example.com
  - path: docs.google.com/spreadsheets/d/my-sheet

groups:
  - name: "Work"
    color: blue          # grey | blue | red | yellow | green | pink | purple | cyan
    collapsed: false     # collapse the group by default?
    rules:
      - domain: github.com          # matches github.com and *.github.com
      - domain: jira.atlassian.net

  - name: "Docs"
    color: green
    rules:
      - path: docs.google.com/document      # matches hostname + path prefix only
      - path: docs.google.com/spreadsheets
```

**Rule types:**

| Type | Example | Matches |
|---|---|---|
| `domain` | `github.com` | `github.com`, `api.github.com`, `gist.github.com` |
| `path` | `docs.google.com/spreadsheets` | Only URLs whose `host/path` starts with that value |

Leading `www.` is stripped automatically on both sides.

---

## How config updates work

```
~/.config/tab-auto-grouper/config.yaml   ← edit this
         │
         │  tabgroups sync
         ▼
~/Library/Application Support/chrome-tab-grouper/extension/config.json
         │
         │  auto-detected within 5 s (no reload needed)
         ▼
      Chrome extension
```

---

## What survives `brew upgrade`

| Path | Owned by | Safe on upgrade? |
|---|---|---|
| Homebrew `libexec/` | Homebrew | Replaced (template only) |
| `~/.config/tab-auto-grouper/config.yaml` | You | **Never touched** |
| `~/Library/Application Support/chrome-tab-grouper/` | You | **Never touched** |

After upgrading, run `tabgroups install` if the extension template changed, then reload in Chrome.

---

## Security

- No external network requests — the extension never contacts a remote server
- No host permissions — cannot read or modify web page content
- No `eval()` or dynamic code execution
- Permissions used: `tabs`, `tabGroups`, `storage` only

---

## Project structure

```
chrome-tab-grouper/
├── extension/              Chrome extension source (template)
│   ├── manifest.json       MV3, minimal permissions
│   ├── background.js       Service worker — reads config.json, groups tabs
│   ├── popup.html/js       Toolbar popup (active groups + reload button)
│   └── icons/              16×16, 48×48, 128×128 PNG icons
├── config.yaml             Default config template (copied to ~/.config on first run)
├── cli.py                  CLI implementation
├── generate_icons.py       Regenerate icons (Python stdlib only, no PIL needed)
└── LICENSE
```
