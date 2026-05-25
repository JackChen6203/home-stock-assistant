# Home Stock Assistant MVP（手機可測）

這版不是只有 Python 腳本，已提供「可用手機直接操作」的 Web App MVP + API：
- 註冊/登入（建立個人帳戶 + SQLite DB）
- 建立家庭與加入家人
- 個人清單與家用清單分離
- 家人購買家用項目會扣家用；不會扣他人個人清單
- Siri 語音可透過捷徑呼叫 `/voice/siri` 新增待購

## 啟動
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 手機測試
1. 安裝 Flutter App 到手機，並把 API_BASE_URL 指向 Render，例如 `https://home-stock-api.onrender.com`。
2. 啟動時可用 `flutter run --dart-define=API_BASE_URL=https://home-stock-api.onrender.com`。
3. 先註冊再登入，登入成功後再新增個人清單與家用清單。
4. 如果你的 Render 網址不是這個網域，直接改成實際網址即可。

## 測試流程（對應你的需求）
1. 建立主使用者 A、家人 B。
2. A `POST /family/create`，再 `POST /family/add-member` 加入 B。
3. A 新增 `personal` 項目：牛奶；新增 `family` 項目：水果。
4. B 呼叫 `POST /purchase` + `for_list_type=family` + `item_name=蘋果`，會扣家用水果。
5. A 的 `personal` 牛奶仍存在（不會被家人購買家用時扣除）。
6. Siri：建立 iOS 捷徑，對 URL `POST http://<電腦IP>:8000/voice/siri`，Header 加 `Authorization: Bearer <token>`，Body：
```json
{"phrase":"阿猴鮮奶","list_type":"personal"}
```
7. 對 Siri 說「嘿 Siri，記購物」，即可把語音結果寫入清單。
