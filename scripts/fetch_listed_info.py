#!/usr/bin/env python
"""Fetch listed info script."""
import sys
from pathlib import Path

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.presentation.cli.commands.fetch_listed_info_command import fetch_listed_info

if __name__ == "__main__":
    fetch_listed_info()