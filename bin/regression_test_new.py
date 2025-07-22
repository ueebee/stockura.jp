#!/usr/bin/env python3
"""
リグレッションテストスクリプト（リファクタリング版）
DBをクリーンな状態にリセットし、主要機能の動作確認を手動/自動で行う
"""
import asyncio
import os
import sys
import argparse
from pathlib import Path

# 新しいモジュール構造をインポート
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from regression_test.config import TestConfig
from regression_test.test_suite import TestSuite
from regression_test.browser import PLAYWRIGHT_AVAILABLE


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Stockura リグレッションテストツール",
        epilog="""
使用例:
  # 手動テストモード（デフォルト）
  python bin/regression_test.py

  # 自動テストモード（Playwrightが必要）
  python bin/regression_test.py --auto

  # ブラウザを表示して自動テスト
  python bin/regression_test.py --auto --visible

  # カスタム設定でテスト
  python bin/regression_test.py --base-url http://localhost:8080 --timeout 120

  # データベースリセットをスキップ
  python bin/regression_test.py --skip-db-reset --auto

環境変数:
  STOCKURA_BASE_URL: テスト対象のベースURL
  DOCKER_COMPOSE_FILE: Docker Composeファイルのパス
  TEST_TIMEOUT: テストタイムアウト時間（秒）
  SCHEDULE_WAIT_MINUTES: スケジュール実行待機時間（分）
        """
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="自動ブラウザテストモードで実行（Playwrightが必要）"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="確認プロンプトをスキップ"
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="ブラウザを表示状態で実行（ヘッドレスモードを無効化）"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("STOCKURA_BASE_URL", "http://localhost:8000"),
        help="テスト対象のベースURL（デフォルト: http://localhost:8000）"
    )
    parser.add_argument(
        "--docker-compose-file",
        default=os.getenv("DOCKER_COMPOSE_FILE", "docker-compose.yml"),
        help="Docker Composeファイルのパス（デフォルト: docker-compose.yml）"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("TEST_TIMEOUT", "60")),
        help="テストタイムアウト時間（秒、デフォルト: 60）"
    )
    parser.add_argument(
        "--schedule-wait",
        type=int,
        default=int(os.getenv("SCHEDULE_WAIT_MINUTES", "2")),
        help="スケジュール実行待機時間（分、デフォルト: 2）"
    )
    parser.add_argument(
        "--skip-db-reset",
        action="store_true",
        help="データベースリセットをスキップ"
    )
    parser.add_argument(
        "--retry-count",
        type=int,
        default=3,
        help="コマンド実行のリトライ回数（デフォルト: 3）"
    )
    parser.add_argument(
        "--report-format",
        choices=["json", "html"],
        default="json",
        help="レポート形式（デフォルト: json）"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="ログレベル（デフォルト: INFO）"
    )
    args = parser.parse_args()

    print("Stockura リグレッションテストツール")
    print("="*60)

    # 設定を作成
    config = TestConfig.from_env()
    config.override_from_args(args)
    
    # 追加の設定
    if hasattr(args, 'report_format'):
        config.report_format = args.report_format
    if hasattr(args, 'log_level'):
        config.log_level = args.log_level
    
    # 設定の検証
    try:
        config.validate()
    except ValueError as e:
        print(f"設定エラー: {e}")
        sys.exit(1)

    if args.auto:
        if PLAYWRIGHT_AVAILABLE:
            print("自動ブラウザテストモードで実行します")
        else:
            print("Playwrightがインストールされていません。")
            print("インストールするには: pip install playwright && playwright install chromium")
            print("手動テストモードで続行します。")
    else:
        print("手動テストモードで実行します")
        print("自動テストを実行するには --auto オプションを使用してください")

    print("="*60)

    # 確認プロンプト
    if not args.no_confirm and not config.skip_db_reset:
        response = input("\nデータベースをリセットして環境を初期化しますか？ (y/N): ")
        if response.lower() != 'y':
            print("テストをキャンセルしました。")
            return

    # テストスイートを作成
    suite = TestSuite(config)

    if args.auto and PLAYWRIGHT_AVAILABLE:
        # 自動テストモード
        success = asyncio.run(suite.run())
    else:
        # 手動テストモード
        if args.auto and not PLAYWRIGHT_AVAILABLE:
            print("\nPlaywrightがインストールされていないため、手動テストモードで実行します")
        
        # データベースリセット（設定により実行）
        if not config.skip_db_reset:
            if not suite.database.reset_database():
                print("データベースのリセットに失敗しました。")
                sys.exit(1)
        
        # 手動テスト手順を表示
        suite.print_manual_test_instructions()
        
        print("\n" + "="*60)
        print("環境の準備が完了しました！")
        print("上記の手順に従って手動テストを実行してください。")
        print("="*60)
        
        success = True
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()