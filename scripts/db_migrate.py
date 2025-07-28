#!/usr/bin/env python
"""Database migration script."""
import sys
from pathlib import Path

# プロジェクトのルートディレクトリを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from app.presentation.cli.commands.migration_command import db_group

if __name__ == "__main__":
    db_group()