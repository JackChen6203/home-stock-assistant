# Home Stock Assistant（管家）

這版提供「手機 app 介面」的 Web App + API。Render 主網址會直接打開管家介面，不再是桌面式測試頁：
- 註冊/登入（建立個人帳戶 + SQLite DB）
- Apple / LINE / Google 登入入口（設定 OAuth 環境變數後啟用）
- 建立家庭與加入家人
- 個人清單與家用清單分離
- 家人購買家用項目會扣家用；不會扣他人個人清單
- Siri 或其他語音助手可透過捷徑 / webhook 呼叫 `/voice/siri` 新增待購，支援「牛奶 2 個」這類數量

## 啟動
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 手機測試
1. 直接用手機瀏覽器開 Render 的主網址，例如 `https://home-stock-api-grzn.onrender.com/`。
2. 先註冊再登入，登入成功後就能新增個人清單、家用清單，或建立家庭與加入成員。
3. 手機瀏覽器可「加入主畫面」，使用體驗會接近 app。

## Apple / LINE / Google 登入
第三方登入需要到各平台建立 OAuth app，並在 Render 設定環境變數後才會真的啟用：

```bash
APPLE_CLIENT_ID=...
APPLE_REDIRECT_URI=https://<your-render-host>/auth/oauth/apple/callback
LINE_CHANNEL_ID=...
LINE_REDIRECT_URI=https://<your-render-host>/auth/oauth/line/callback
GOOGLE_CLIENT_ID=...
GOOGLE_REDIRECT_URI=https://<your-render-host>/auth/oauth/google/callback
```

目前 API 已提供 `/auth/oauth/{provider}/start` 產生授權網址；未設定時 app 會明確提示尚未啟用。

## 測試流程（對應你的需求）
1. 建立主使用者 A、家人 B。
2. A `POST /family/create`，再 `POST /family/add-member` 加入 B。
3. A 新增 `personal` 項目：牛奶；新增 `family` 項目：水果。
4. B 呼叫 `POST /purchase` + `for_list_type=family` + `item_name=蘋果`，會扣家用水果。
5. A 的 `personal` 牛奶仍存在（不會被家人購買家用時扣除）。
6. Siri：建立 iOS 捷徑，對 URL `POST https://<your-render-host>/voice/siri`，Header 加 `Authorization: Bearer <token>`，Body：
```json
{"phrase":"幫我在管家紀錄要買阿猴鮮奶 2 個","list_type":"personal"}
```
7. 對 Siri 說「嘿 Siri，記購物」，即可把語音結果寫入清單。
