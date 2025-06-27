# J-Quants API - Listed Info エンドポイント仕様

## 基本情報
- **エンドポイント**: `https://api.jquants.com/v1/listed/info`
- **HTTPメソッド**: GET
- **概要**: 上場銘柄一覧を取得するAPI

## リクエストパラメータ

| パラメータ | 必須 | 型 | 説明 |
|-----------|------|-----|------|
| `code` | オプション | string | 4桁の銘柄コード。普通株式と優先株式がある場合は普通株式のみ返却 |
| `date` | オプション | string | 基準となる日付（YYYYMMDD または YYYY-MM-DD） |

## レスポンス構造

```json
{
    "info": [
        {
            "Date": "日付",
            "Code": "銘柄コード", 
            "CompanyName": "会社名",
            "CompanyNameEnglish": "会社名（英語）",
            "Sector17Code": "17業種コード",
            "Sector17CodeName": "17業種コード名",
            "Sector33Code": "33業種コード",
            "Sector33CodeName": "33業種コード名", 
            "ScaleCategory": "規模コード",
            "MarketCode": "市場区分コード",
            "MarketCodeName": "市場区分名",
            "MarginCode": "貸借信用区分",
            "MarginCodeName": "貸借信用区分名"
        }
    ]
}
```

## 使用例

### cURL
```bash
idToken=<YOUR idToken> && curl https://api.jquants.com/v1/listed/info -H "Authorization: Bearer $idToken"
```

### Python
```python
import requests

idToken = "YOUR idToken"
headers = {'Authorization': 'Bearer {}'.format(idToken)}
r = requests.get("https://api.jquants.com/v1/listed/info", headers=headers)
```

## 認証
- Bearer認証を使用
- idTokenが必要

## 注意事項
- 普通株式と優先株式がある場合、普通株式のみが返却される
- 日付パラメータは YYYYMMDD または YYYY-MM-DD 形式で指定可能