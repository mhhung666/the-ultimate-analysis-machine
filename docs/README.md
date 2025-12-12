# Market Intelligence System - GitHub Pages

這是 Market Intelligence System 的靜態網站版本。

## 頁面結構

- **首頁** ([index.html](index.html)): 系統介紹和導航
- **市場分析** ([market.html](market.html)): 全球市場深度分析報告
- **持倉分析** ([holdings.html](holdings.html)): 個人投資組合分析報告

## 部署方式

1. 在 GitHub repository 設定中啟用 GitHub Pages
2. 選擇 `docs` 資料夾作為來源
3. 網站將自動部署到 `https://<username>.github.io/<repository>/`

## 本地預覽

在 `docs` 目錄下啟動本地伺服器:

```bash
cd docs
python -m http.server 8000
```

然後在瀏覽器訪問 `http://localhost:8000`

## 更新報告

當有新的分析報告時:

1. 將新的 markdown 報告轉換為 HTML
2. 更新 `market.html` 或 `holdings.html`
3. 提交並推送到 GitHub
4. GitHub Pages 會自動更新

## 技術棧

- 純 HTML/CSS
- 響應式設計
- 深色主題
- 支援中文顯示
