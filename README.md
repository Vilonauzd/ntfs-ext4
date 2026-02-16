# NTFS → EXT4 Forensic Copy Tool

**Author:** jm@qvert.net  
**Version:** 1.0.0  
**License:** MIT  

A forensic-grade GUI tool for safely copying data from NTFS filesystems (via `ntfs-3g`) to native Linux EXT4 filesystems with full audit logging, hidden file preservation, and post-copy verification.

---

##  Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [Technical Details](#-technical-details)
- [Safety & Warnings](#-safety--warnings)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

---

##  Features

| Feature | Description |
|---------|-------------|
| **Hidden File Preservation** | Copies ALL dotfiles (`.git`, `.ssh`, `.env`, etc.) - not excluded |
| **Unlimited Recursion Depth** | No directory depth limits via `rsync -a` + `os.walk` |
| **NTFS Artifact Exclusion** | Only excludes system junk (`.Trashes`, `$RECYCLE.BIN`, `Thumbs.db`, etc.) |
| **Pre-Copy Forensic Scan** | Detects hidden files, case conflicts, file counts before copying |
| **Post-Copy Verification** | Validates sample files, hidden artifact counts, permissions |
| **Case Sensitivity Detection** | Warns about NTFS/ext4 case conflict risks before copy |
| **Timestamped Audit Log** | Full immutable log with session metadata for compliance |
| **No Root Required** | Operates entirely on user-owned mounts (`/media/$USER/*`) |
| **Dynamic UI Scaling** | Large fonts, symmetrical padding, resizable window |
| **Real-Time Progress** | Live `rsync` output streaming to GUI log |

---

##  Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Ubuntu 22.04+ / Zorin OS 16+ | Ubuntu 24.04+ / Zorin OS 17+ |
| **RAM** | 4 GB | 8 GB+ (for large transfers) |
| **Disk Space** | Sufficient free space on destination | 20% buffer recommended |
| **Display** | 1280×720 resolution | 1920×1080+ (full UI visibility) |

### Software Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| `python3` (≥3.8) | Runtime environment | ✅ Yes |
| `python3-tk` | Tkinter GUI library | ✅ Yes |
| `rsync` | File synchronization engine | ✅ Yes |
| `ntfs-3g` | NTFS read/write support | ✅ Yes (for source) |
| `chmod` (coreutils) | Permission management | ✅ Yes |

### Verify Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check Tkinter availability
python3 -c "import tkinter; print('Tkinter OK')"

# Check rsync
rsync --version

# Check ntfs-3g (for NTFS source mounts)
ntfs-3g --version
```

---

##  Installation

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-tk rsync ntfs-3g coreutils
```

### 2. Clone or Download Script

```bash
# Option A: Clone from repository
git clone https://github.com/jm-qvert/ntfs-to-ext4-copy.git
cd ntfs-to-ext4-copy

# Option B: Download directly
wget https://raw.githubusercontent.com/jm-qvert/ntfs-to-ext4-copy/main/copy_convert_ntfs_ext4.py
```

### 3. Make Executable

```bash
chmod +x copy_convert_ntfs_ext4.py
```

### 4. (Optional) Create Desktop Shortcut

```bash
cat <<'EOF' | tee ~/Desktop/NTFS-to-EXT4.desktop
[Desktop Entry]
Name=NTFS to EXT4 Copy
Comment=Forensic NTFS to EXT4 file copier
Exec=/home/jm/Desktop/copy_convert_ntfs_ext4.py
Icon=drive-harddisk
Terminal=false
Type=Application
Categories=Utility;System;
EOF

chmod +x ~/Desktop/NTFS-to-EXT4.desktop
```

---

##  Usage

### Launch the Application

```bash
./copy_convert_ntfs_ext4.py
```

### Step-by-Step Workflow

1. **Verify Source Path**  
   Default: `/media/jm/NAS/GITHUB_REPOS` (NTFS via `ntfs-3g`)  
   Click **Browse** to select different source directory

2. **Verify Destination Path**  
   Default: `/media/jm/SAMSUNG9801TB/GITHUB_REPOS` (EXT4)  
   Click **Browse** to select different destination parent

3. **Review Pre-Copy Scan**  
   After clicking **Start Copy**, the tool will:
   - Count total files/directories
   - Detect hidden files (`.git`, `.ssh`, etc.)
   - Identify case sensitivity conflicts
   - Calculate total data size

4. **Confirm Copy Operation**  
   Review the confirmation dialog showing:
   - File count
   - Total size in GB
   - Hidden file preservation status
   - Case conflict warnings

5. **Monitor Copy Progress**  
   Watch real-time `rsync` output in the Audit Log panel

6. **Review Post-Copy Verification**  
   After completion, verify:
   - Sample file sizes match
   - Hidden artifact count preserved
   - Permissions set correctly (`u=rwX,g=rX,o=rX`)

---

##  Technical Details

### Rsync Command Structure

```bash
rsync -avh --progress --stats --exclude-from=- SOURCE/ DESTINATION/
```

| Flag | Purpose |
|------|---------|
| `-a` | Archive mode (preserves timestamps, symlinks, permissions) |
| `-v` | Verbose output (file-by-file listing) |
| `-h` | Human-readable sizes |
| `--progress` | Real-time transfer progress |
| `--stats` | Detailed transfer statistics |
| `--exclude-from=-` | Read exclusions from stdin (NTFS system artifacts only) |

### Exclusion Policy

**Excluded (NTFS System Artifacts):**
- `.Trashes`
- `$RECYCLE.BIN`
- `System Volume Information`
- `desktop.ini`
- `Thumbs.db` (+ variants)
- `ehthumbs.db` (+ variants)

**Preserved (User Dotfiles):**
- `.git/`
- `.ssh/`
- `.env`
- `.bashrc`, `.profile`
- `.config/`
- All other `.*` files/directories

### Permission Model

```bash
chmod -R u=rwX,g=rX,o=rX /destination/path
```

| Class | Permissions | Rationale |
|-------|-------------|-----------|
| **User (u)** | `rwX` | Full read/write/execute (owner) |
| **Group (g)** | `rX` | Read + execute (traverse directories) |
| **Other (o)** | `rX` | Read + execute (minimal access) |

>  **No sudo required** - Tool operates on user-owned mounts only

### Case Sensitivity Handling

| Filesystem | Behavior |
|------------|----------|
| **NTFS** | Case-preserving but **case-insensitive** |
| **EXT4** | **Case-sensitive** |

**Risk:** If source contains both `File.txt` and `file.txt` in same directory:
- NTFS treats as **same file** (last write wins)
- EXT4 treats as **distinct files** (both preserved)

**Mitigation:** Tool detects and logs conflicts during pre-copy scan for manual validation.

---

##  Safety & Warnings

### Critical Safety Rules

| Rule | Reason |
|------|--------|
| **DO NOT run as root** | Risks permission corruption on destination |
| **Verify mount paths** | Ensure `/media/$USER/*` are user-owned |
| **Check destination space** | Insufficient space causes partial copies |
| **Review case conflicts** | NTFS/ext4 differences may cause unexpected duplicates |
| **Don't interrupt mid-copy** | May leave destination in inconsistent state |

### What This Tool Does NOT Do

-  Does **not** convert filesystem formats (copies files only)
-  Does **not** modify source data (read-only operations)
-  Does **not** handle encrypted NTFS volumes (BitLocker unsupported)
-  Does **not** replace backup solutions (verify critical data independently)

---

## Troubleshooting

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'tkinter'` | `python3-tk` not installed | `sudo apt install python3-tk` |
| `Error: Layout Horizontal.horizontal.TProgressbar not found` | Invalid ttk style name | Use latest script version (fixed) |
| `Permission denied` on destination | Mount owned by root | Remount with user ownership or use `/media/$USER/` |
| `rsync: command not found` | `rsync` not installed | `sudo apt install rsync` |
| Source path not readable | NTFS mount failed | Check `ntfs-3g` installation and mount status |
| Window appears cut off | Display resolution too low | Use 1920×1080+ or resize window manually |

### Diagnostic Commands

```bash
# Check mount ownership
ls -ld /media/jm/NAS

# Verify rsync availability
which rsync

# Test Tkinter import
python3 -c "import tkinter; tkinter.Tk()"

# Check available disk space
df -h /media/jm/SAMSUNG9801TB

# View system logs for mount errors
dmesg | grep -i ntfs
```

### Log File Location

Audit logs are displayed in the GUI only (not saved to disk by default). To preserve logs:

1. Select all text in Audit Log panel (`Ctrl+A`)
2. Copy (`Ctrl+C`)
3. Paste into text file for archival

---

## ❓ FAQ

**Q: Why not use `ntfs3` kernel driver instead of `ntfs-3g`?**  
A: Some distributions (including Zorin) default to `ntfs-3g` for stability. This tool supports both - just ensure your NTFS volume is mounted and accessible.

**Q: Can I copy symbolic links?**  
A: Yes - `rsync -a` preserves symlinks. They will be recreated on the EXT4 destination.

**Q: What happens if the copy is interrupted?**  
A: Rsync supports resumption. Simply re-run the copy - existing files will be skipped, only missing/changed files will transfer.

**Q: Is the destination bootable after copy?**  
A: No - this tool copies **files only**, not boot sectors or partition tables. For system migrations, use Clonezilla or similar.

**Q: Can I modify the exclusion list?**  
A: Yes - edit the `NTFS_EXCLUSIONS` list in the script (around line 25). Do not exclude user dotfiles unless intentional.

**Q: Does this work over network mounts (SMB/CIFS)?**  
A: Technically yes, but not recommended. Network latency affects rsync performance and verification accuracy. Use for direct-attached storage only.

---

## Support

- **Author:** jm@qvert.net
- **Issues:** Report via repository issue tracker
- **Contributions:** Pull requests welcome

---

## License

MIT License - See LICENSE file for details.

---

## Acknowledgments

- `rsync` development team
- Python Tkinter maintainers
- NTFS-3G project contributors
- Linux filesystem community

---

**Last Updated:** 2026  
**Tested On:** Ubuntu 24.04, Zorin OS 17
