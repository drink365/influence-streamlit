# 影響力｜永傳家族傳承平台（MVP • Streamlit）

> 一個可立即上線驗證的 MVP：首頁 → AI 診斷 → 結果 → 預約；同時含顧問專區與收費頁。
> 合規設計：不涉佣分潤（僅授權與專業服務）。

## 主要頁面
- `Home`（首頁與雙入口 CTA）
- `Diagnostic`（傳承風險與資產概況表單，產生 CaseID）
- `Result`（根據表單輸入生成簡版結果與「立即預約」）
- `Book`（預約頁：可嵌入 Calendly 或填寫表單）
- `Advisors`（顧問專區：註冊、登入並建立個案）
- `Plans`（授權與高階會員方案，合規收費階梯）
- `Privacy`（隱私與免責）

## 快速啟動
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署到 Streamlit Cloud
1. 將此資料夾推到 GitHub repo
2. 到 https://share.streamlit.io 連結你的 repo，入口點設為 `app.py`

## 合規聲明
- 平台不提供佣金分潤；顧問端僅收授權費與專業服務費。
- 所有計算為初步試算示意，最終以專業顧問複核與各項法令為準。
