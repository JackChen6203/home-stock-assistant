# Home Stock Assistant MVP（雲端 + 手機 App）

你提到不想用「電腦 IP」測試，這版已改成 **雲端部署** 方案，手機直接連雲端網域。

## 已完成項目
- FastAPI 後端（支援雲端 DB）
- DATABASE_URL 環境變數連接（Render Postgres / Supabase Postgres 都可）
- 手機端程式（Flutter）：`mobile/`
- Render 部署設定：`infra/render.yaml`
- 家庭/個人清單分離與購買扣除
- Siri endpoint：`POST /voice/siri`

## 1) 部署雲服務（Render）
1. 將此 repo push 到 GitHub。
2. 到 Render 建立 Blueprint，選 `infra/render.yaml`。
3. Render 會自動建立：
   - Web Service: `home-stock-api`
   - Postgres: `home-stock-db`
4. 部署完成後，取得 API 網址，例如：
   - `https://home-stock-api.onrender.com`

## 2) 手機 App（Flutter）
1. 安裝 Flutter SDK。
2. 進入 `mobile/`：
```bash
flutter pub get
flutter run
```
3. App 首頁將 `API Base URL` 改成你的 Render 網址。
4. 註冊/登入後即可操作個人/家用清單。

## 3) Siri 串接（iPhone）
1. iOS「捷徑」新增快捷指令。
2. 動作：`取得 URL 內容`（POST）
3. URL: `https://<你的網域>/voice/siri`
4. Header: `Authorization: Bearer <login token>`
5. JSON Body:
```json
{"phrase":"阿猴鮮奶","list_type":"personal"}
```
6. 用 Siri 觸發捷徑後，即可新增到清單。

## 4) 你要的行為對應
- 註冊登入 + 建帳戶 + DB：`/auth/register`, `/auth/login`
- 家人共用清單，購買扣家用不扣個人：`/family/*`, `/purchase`
- Siri 語音加入待購：`/voice/siri`
