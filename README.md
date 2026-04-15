# Software Version Management System

A Python-based CLI application for tracking and managing software component versions in a DevOps environment.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [Components](#components)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [CSV Data Format](#csv-data-format)
- [Version Comparison Logic](#version-comparison-logic)

---

## Overview

This project demonstrates core Python concepts applied to a real-world DevOps scenario: tracking installed software versions, comparing them against desired target versions, and managing update actions (upgrade / downgrade / no change).

---

## Project Structure

```
Python_Final_Lab/
│
├── main.py               # Entry point — main menu and navigation
├── display_data.py       # Display components and handle version updates
├── csv_manager.py        # CSV read/write operations for version data
├── compare_versions.py   # Version comparison logic
│
├── versions.csv          # Current installed versions (auto-created if missing)
├── version_history.csv   # History log of past version updates
│
└── README.md             # Project documentation
```

---

## Features

- **View installed versions** — displays all tracked components with status and last update date
- **Update versions** — manually enter desired versions or load from CSV
- **Version comparison** — smart digit-by-digit comparison to determine: `upgrade`, `downgrade`, or `not required`
- **Persistent storage** — all changes are saved to CSV files
- **Update history** — every change is logged with a timestamp
- **Input validation** — graceful error handling and fallback to defaults

---

## Components

| Module | Responsibility |
|--------|---------------|
| `main.py` | Menu loop, routing, program entry point |
| `display_data.py` | Show version table, accept desired version input |
| `csv_manager.py` | Load/save `versions.csv` and `version_history.csv` |
| `compare_versions.py` | Compare installed vs desired versions digit by digit |

---

## Getting Started

### Prerequisites

- Python 3.x (no external packages required — uses only standard library)

### Run the Application

```bash
python main.py
```

---

## Usage

After launching, you will see the main menu:

```
======================================================================
SOFTWARE VERSION MANAGEMENT SYSTEM
======================================================================

1. Display installed versions
2. Update versions
3. Exit
======================================================================
```

### Option 1 — Display Installed Versions

Shows a table of all tracked components:

```
Component       Version              Status          Last Update
----------------------------------------------------------------------
OS              10.2                 ● INITIAL        2026-04-14 10:00:00
BE              10.0.19042           ● INITIAL        2026-04-14 10:00:00
DB              12.1                 ● INITIAL        2026-04-14 10:00:00
FW              3.5.1                ● INITIAL        2026-04-14 10:00:00
```

### Option 2 — Update Versions

Enter desired target versions for each component. The system compares them against installed versions and logs the result.

---

## CSV Data Format

### `versions.csv`

| Column | Description |
|--------|-------------|
| `Component` | Component identifier (e.g. `OS`, `DB`) |
| `CurrentVersion` | Currently installed version string |
| `LastUpdateDate` | Timestamp of last update |
| `PreviousVersion` | Version before the last update |
| `UpdateStatus` | `initial`, `updated`, etc. |

### Default Components

| Component | Description |
|-----------|-------------|
| `OS` | Operating System |
| `BE` | Backend Service |
| `DB` | Database |
| `FW` | Firmware |

---

## Version Comparison Logic

Versions are compared digit by digit (left to right), supporting variable-length version strings:

| Result | Condition | Action |
|--------|-----------|--------|
| `upgrade` | installed < desired | Update to newer version |
| `downgrade` | installed > desired | Roll back to older version |
| `not required` | installed == desired | No action needed |
| `missing` | component not in desired list | Flagged as missing |

**Example:**

```python
installed = {'OS': '10.2', 'DB': '12.1'}
desired   = {'OS': '10.3', 'DB': '12.1'}

# Result:
# OS → upgrade
# DB → not required
```

---

## Author

**tareqa2** — [github.com/tareqa2](https://github.com/tareqa2)
