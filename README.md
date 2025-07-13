# sam-sample-wikipedia-scraper

AWS SAM を使用したWikipediaスクレイピングREST APIの教育用サンプル

## 概要

Wikipedia記事のURLを指定して目次情報をJSON形式で取得するサーバーレスAPI

## 機能

### エンドポイント

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/toc?url={wikipedia_url}` | 指定されたWikipedia URLの目次情報を取得 |

### リクエスト例

```bash
curl "https://your-api-gateway-url/toc?url=https://ja.wikipedia.org/wiki/Amazon_Web_Services"
```

### レスポンス例

```json
{
  "success": true,
  "url": "https://ja.wikipedia.org/wiki/Amazon_Web_Services",
  "title": "Amazon Web Services",
  "toc": [
    {
      "level": 1,
      "title": "概要",
      "anchor": "概要",
      "href": "#概要"
    },
    {
      "level": 2,
      "title": "初期の開発",
      "anchor": "初期の開発",
      "href": "#初期の開発"
    },
    {
      "level": 3,
      "title": "Amazon EC2",
      "anchor": "Amazon_EC2",
      "href": "#Amazon_EC2"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## セットアップ

### 前提条件
- AWS CLI 設定済み
- SAM CLI インストール済み
- Python 3.9+

### デプロイ手順

```bash
# リポジトリクローン
git clone https://github.com/yourusername/sam-sample-wikipedia-scraper.git
cd sam-sample-wikipedia-scraper

# ビルド・デプロイ
sam build
sam deploy --guided
```

### ローカルテスト

```bash
# ローカル起動
sam local start-api

# テスト実行
curl "http://localhost:3000/toc?url=https://ja.wikipedia.org/wiki/Amazon_Web_Services"
```

## プロジェクト構造

```
sam-sample-wikipedia-scraper/
├── toc_scraper/
│   ├── app.py              # Lambda関数メイン処理
│   ├── wikipedia_toc.py    # 目次スクレイピング処理
│   └── requirements.txt
├── template.yaml           # SAMテンプレート
└── tests/
```

## 使用技術

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **AWS** | SAM, Lambda, API Gateway | サーバーレス基盤 |
| **Python** | Beautiful Soup, Requests | HTMLパース, HTTP通信 |

## 重要事項

### robots.txt遵守

| 項目 | 制限 | 対応 |
|------|------|------|
| **対象URL** | `/wiki/記事名` のみ | URLパターンチェック |
| **禁止パス** | `/w/`, `/api/`, `Special:`, 利用者ページ | アクセス拒否 |
| **レート制限** | 適切な間隔 | 1-2秒待機 |
| **User-Agent** | 識別可能な文字列 | `Educational-TOC-Scraper/1.0` |

### ライセンス
- 本プロジェクト: MIT License
- Wikipedia記事: CC BY-SA 3.0

## 参考リンク
- [AWS SAM ドキュメント](https://docs.aws.amazon.com/serverless-application-model/)
- [Wikipedia robots.txt](https://ja.wikipedia.org/robots.txt)