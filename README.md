# sam-sample-wikipedia-scraper

AWS SAM を使用したWikipediaスクレイピングREST APIの教育用サンプル

## 概要

Wikipedia記事のURLを指定して目次情報をJSON形式で取得するサーバーレスAPI
**Wikipedia の robots.txt を厳格に遵守した実装**

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
  "total_items": 3,
  "robots_compliance": "This service respects Wikipedia's robots.txt",
  "user_agent": "Educational-TOC-Scraper/1.0 (Contact: educational.purpose@example.com)"
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
│   └── requirements.txt
├── template.yaml           # SAMテンプレート
└── tests/
```

## 使用技術

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| **AWS** | SAM, Lambda, API Gateway | サーバーレス基盤 |
| **Python** | Beautiful Soup, Requests, lxml | HTMLパース, HTTP通信 |

## robots.txt 遵守の実装詳細

### 厳格なURL検証

| 禁止パス | 対応 | 理由 |
|---------|------|------|
| `/w/` | アクセス拒否 | robots.txt明示的禁止 |
| `/api/` | アクセス拒否 | robots.txt明示的禁止 |
| `/trap/` | アクセス拒否 | robots.txt明示的禁止 |
| `Special:`, `特別:` | アクセス拒否 | 特別ページ（多言語対応） |
| `User:`, `利用者:` | アクセス拒否 | ユーザーページ（多言語対応） |
| `Talk:`, `ノート:` | アクセス拒否 | 議論ページ（多言語対応） |
| `Template:` | アクセス拒否 | テンプレート |
| `Module:` | アクセス拒否 | モジュール |
| `MediaWiki:` | アクセス拒否 | システムページ |
| `WP:`, `LTA:` | アクセス拒否 | Wikipedia名前空間ショートカット |

### 日本語Wikipedia特有の禁止パターン

| 日本語パターン | 英語パターン | 理由 |
|---------------|-------------|------|
| `削除依頼` | `Articles_for_deletion` | 削除議論ページ |
| `投稿ブロック依頼` | `Requests_for_adminship` | ブロック依頼 |
| `管理者伝言板` | `Administrator_noticeboard` | 管理者連絡 |
| `利用者‐会話:` | `User_talk:` | 利用者議論 |
| `削除の復帰依頼` | `Deletion_review` | 削除復帰依頼 |

### URLエンコーディング対応

実装では以下のURLエンコードパターンも検出・拒否します：
- `%E5%89%8A%E9%99%A4%E4%BE%9D%E9%A0%BC`（削除依頼）
- `%E5%88%A9%E7%94%A8%E8%80%85`（利用者）
- `%E7%89%B9%E5%88%A5`（特別）
- `%3A`（コロン）

### レート制限とUser-Agent

| 項目 | 設定値 | 目的 |
|------|--------|------|
| **最小待機時間** | 1.0秒 | サーバー負荷軽減 |
| **User-Agent** | `Educational-TOC-Scraper/1.0` | 識別可能な文字列 |
| **タイムアウト** | 10秒 | 適切なリクエスト制限 |
| **リトライ** | なし | 過度なアクセス防止 |

### ライセンス
- 本プロジェクト: MIT License
- Wikipedia記事: CC BY-SA 3.0

## 重要事項

**このAPIは教育目的で作成されており、Wikipedia の robots.txt を厳格に遵守しています。**

1. ✅ 許可されたパス（`/wiki/記事名`）のみアクセス
2. ✅ 適切なUser-Agent設定
3. ✅ レート制限実装（1秒間隔）
4. ✅ 禁止パスの完全ブロック
5. ✅ エラーハンドリング

## 参考リンク
- [Wikipedia robots.txt](https://ja.wikipedia.org/robots.txt)
- [AWS SAM ドキュメント](https://docs.aws.amazon.com/serverless-application-model/)
- [Beautiful Soup ドキュメント](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)