# clinic_appointment

用 Flask + SQL Server + HTML/CSS 製作的「醫院預約掛號系統」。  
提供病人初診登記、預約掛號、查詢／修改／取消預約，以及顯示醫師班表與預約人數。  

## 專案結構  

```

clinic_appointment/
├─ app.py            # Flask 主程式（路由、邏輯）
├─ config.py         # 資料庫連線設定
├─ requirements.txt  # Python 套件需求
└─ templates/        # HTML 樣板
├─ index.html
├─ appointment.html
├─ new_patient.html
├─ my_appointments.html
├─ doctor_schedule.html

````

## 安裝與啟動  

1. Clone 此專案：  

   git clone https://github.com/yijean333/clinic_appointment.git
   cd clinic_appointment

2. 建立虛擬環境並安裝依賴：

   python -m venv venv
   source venv/bin/activate   # Linux/Mac  
   venv\Scripts\activate      # Windows  
   pip install -r requirements.txt

3. 修改 `config.py`，設定好 SQL Server 的 DSN／帳號密碼／資料庫名稱

4. 啟動 Flask：

   python app.py

   然後在瀏覽器打開 `http://127.0.0.1:5000/`




如果你同意，我幫你再加一個「簡易流程圖 (flow) + ERD (資料表關聯圖)」段落到 README，讓整個專案更完整。
