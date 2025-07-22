"""
テストレポート生成モジュール
テスト結果をJSON/HTML形式でレポート出力
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import TestConfig
from .utils import setup_logger, TestResult, format_duration, ensure_dir


class TestReporter:
    """テストレポート生成クラス"""
    
    def __init__(self, config: TestConfig):
        """
        Args:
            config: テスト設定
        """
        self.config = config
        self.logger = setup_logger(self.__class__.__name__, config.log_level, config.log_file)
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.report_dir = ensure_dir(config.report_dir)
        
    def add_result(self, result: TestResult):
        """テスト結果を追加
        
        Args:
            result: テスト結果
        """
        self.results.append(result)
        self.logger.debug(f"テスト結果を追加: {result.name} - {result.status}")
    
    def finalize(self):
        """レポートを確定"""
        self.end_time = datetime.now()
    
    def generate_summary(self) -> Dict[str, Any]:
        """サマリー情報を生成
        
        Returns:
            サマリー辞書
        """
        if not self.end_time:
            self.finalize()
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == "SUCCESS")
        failed_tests = sum(1 for r in self.results if r.status == "FAILED")
        skipped_tests = sum(1 for r in self.results if r.status == "SKIPPED")
        
        duration = (self.end_time - self.start_time).total_seconds()
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "test_date": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": format_duration(duration),
            "duration_seconds": duration,
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "success_rate": round(success_rate, 2),
            "environment": {
                "base_url": self.config.base_url,
                "docker_compose_file": self.config.docker_compose_file,
                "test_timeout": self.config.test_timeout,
                "schedule_wait_minutes": self.config.schedule_wait_minutes,
                "headless": self.config.headless,
                "test_data_source": self.config.test_data_source
            }
        }
    
    def save_json_report(self) -> str:
        """JSON形式のレポートを保存
        
        Returns:
            保存したファイルパス
        """
        summary = self.generate_summary()
        
        report = {
            **summary,
            "results": [result.to_dict() for result in self.results]
        }
        
        # ファイル名を生成
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"regression_test_report_{timestamp}.json"
        filepath = self.report_dir / filename
        
        # JSONファイルとして保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"JSONレポートを保存: {filepath}")
        return str(filepath)
    
    def save_html_report(self) -> str:
        """HTML形式のレポートを保存
        
        Returns:
            保存したファイルパス
        """
        summary = self.generate_summary()
        
        # HTMLテンプレート
        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>リグレッションテストレポート - {summary['test_date']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background-color: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
            border: 1px solid #e9ecef;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 14px;
            font-weight: normal;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            margin: 0;
        }}
        .success {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #6c757d; }}
        .warning {{ color: #ffc107; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-success {{
            background-color: #d4edda;
            color: #155724;
        }}
        .badge-danger {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .badge-secondary {{
            background-color: #e2e3e5;
            color: #383d41;
        }}
        .error-list {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .error-list li {{
            color: #dc3545;
            margin: 5px 0;
        }}
        .environment {{
            background-color: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin-top: 20px;
        }}
        .environment h3 {{
            margin-top: 0;
            color: #495057;
        }}
        .environment dl {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            margin: 0;
        }}
        .environment dt {{
            font-weight: 600;
            color: #6c757d;
        }}
        .environment dd {{
            margin: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>リグレッションテストレポート</h1>
        
        <div class="summary">
            <div class="summary-card">
                <h3>総テスト数</h3>
                <p class="value">{summary['total_tests']}</p>
            </div>
            <div class="summary-card">
                <h3>成功</h3>
                <p class="value success">{summary['passed']}</p>
            </div>
            <div class="summary-card">
                <h3>失敗</h3>
                <p class="value failed">{summary['failed']}</p>
            </div>
            <div class="summary-card">
                <h3>スキップ</h3>
                <p class="value skipped">{summary['skipped']}</p>
            </div>
            <div class="summary-card">
                <h3>成功率</h3>
                <p class="value {'success' if summary['success_rate'] >= 80 else 'warning' if summary['success_rate'] >= 50 else 'failed'}">{summary['success_rate']}%</p>
            </div>
            <div class="summary-card">
                <h3>実行時間</h3>
                <p class="value">{summary['duration']}</p>
            </div>
        </div>
        
        <h2>テスト結果詳細</h2>
        <table>
            <thead>
                <tr>
                    <th>テスト名</th>
                    <th>ステータス</th>
                    <th>実行時間</th>
                    <th>詳細</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # 各テスト結果を追加
        for result in self.results:
            status_badge = {
                "SUCCESS": ("badge-success", "成功"),
                "FAILED": ("badge-danger", "失敗"),
                "SKIPPED": ("badge-secondary", "スキップ")
            }.get(result.status, ("badge-secondary", result.status))
            
            duration_str = f"{result.duration:.1f}秒" if result.duration else "-"
            
            # 詳細情報
            details_html = ""
            if result.errors:
                details_html += '<ul class="error-list">'
                for error in result.errors:
                    details_html += f'<li>{self._escape_html(error)}</li>'
                details_html += '</ul>'
            
            if result.details:
                for key, value in result.details.items():
                    if key != 'skip_reason':
                        details_html += f'<div><strong>{key}:</strong> {value}</div>'
            
            if result.status == "SKIPPED" and 'skip_reason' in result.details:
                details_html = f'<div>理由: {result.details["skip_reason"]}</div>'
            
            html_content += f"""
                <tr>
                    <td>{self._escape_html(result.name)}</td>
                    <td><span class="badge {status_badge[0]}">{status_badge[1]}</span></td>
                    <td>{duration_str}</td>
                    <td>{details_html}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
        
        <div class="environment">
            <h3>実行環境</h3>
            <dl>
                <dt>実行日時</dt>
                <dd>{test_date}</dd>
                <dt>ベースURL</dt>
                <dd>{base_url}</dd>
                <dt>Docker Compose</dt>
                <dd>{docker_compose_file}</dd>
                <dt>テストタイムアウト</dt>
                <dd>{test_timeout}秒</dd>
                <dt>ヘッドレスモード</dt>
                <dd>{headless}</dd>
                <dt>データソース</dt>
                <dd>{test_data_source}</dd>
            </dl>
        </div>
    </div>
</body>
</html>
""".format(
            test_date=summary['test_date'],
            base_url=summary['environment']['base_url'],
            docker_compose_file=summary['environment']['docker_compose_file'],
            test_timeout=summary['environment']['test_timeout'],
            headless="有効" if summary['environment']['headless'] else "無効",
            test_data_source=summary['environment']['test_data_source']
        )
        
        # ファイル名を生成
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"regression_test_report_{timestamp}.html"
        filepath = self.report_dir / filename
        
        # HTMLファイルとして保存
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTMLレポートを保存: {filepath}")
        return str(filepath)
    
    def save_report(self) -> str:
        """設定に応じた形式でレポートを保存
        
        Returns:
            保存したファイルパス
        """
        if self.config.report_format == "html":
            return self.save_html_report()
        else:
            return self.save_json_report()
    
    def print_console_summary(self):
        """コンソールにサマリーを出力"""
        summary = self.generate_summary()
        
        print("\n" + "="*60)
        print("自動テスト結果サマリー")
        print("="*60)
        print(f"実行日時: {summary['test_date']}")
        print(f"実行時間: {summary['duration']}")
        print(f"総テスト数: {summary['total_tests']}")
        print(f"成功: {summary['passed']}")
        print(f"失敗: {summary['failed']}")
        print(f"スキップ: {summary['skipped']}")
        print(f"成功率: {summary['success_rate']}%")
        print("="*60)
        
        for result in self.results:
            status_mark = {
                "SUCCESS": "✅",
                "FAILED": "❌",
                "SKIPPED": "⏭️"
            }.get(result.status, "❓")
            
            print(f"{status_mark} {result.name}")
            
            if result.status == "FAILED":
                for error in result.errors:
                    print(f"   - {error}")
            elif result.status == "SUCCESS" and result.details:
                # 成功したテストの主要な詳細情報
                for key, value in result.details.items():
                    if key in ['manual_sync', 'daily_schedule_created', 'company_schedule_created']:
                        if value:
                            print(f"   - {key}: ✓")
            elif result.status == "SKIPPED" and 'skip_reason' in result.details:
                print(f"   - スキップ理由: {result.details['skip_reason']}")
        
        print("="*60)
    
    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ
        
        Args:
            text: エスケープ対象テキスト
            
        Returns:
            エスケープ済みテキスト
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))