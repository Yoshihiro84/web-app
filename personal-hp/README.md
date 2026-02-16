# personal-hp

GitHub Pagesで公開できる、自己紹介+研究実績向けの静的サイトテンプレートです。

## ファイル構成

```txt
personal-hp/
├─ index.html
├─ profile.html
├─ publications.html
├─ assets/
│  ├─ css/style.css
│  └─ js/main.js
└─ data/
   └─ achievements.json
```

## 編集ポイント

- 名前や所属: `index.html`, `profile.html`
- 連絡先メール: 各HTMLの `mailto:your-email@example.com`
- GitHubリンク: 各HTMLの `https://github.com/your-account`
- CV: `assets/cv.pdf` を配置し、各HTMLのリンクを利用
- 実績データ: `data/achievements.json`
- 入力シート: `data/input-template.md`（これを埋めれば反映しやすい）

## GitHub Pages公開

1. この `personal-hp/` 配下を公開用リポジトリにpush
2. GitHubの `Settings > Pages` を開く
3. `Deploy from a branch` を選び、`main` と `/ (root)` を指定
4. 数分待って公開URLにアクセス
