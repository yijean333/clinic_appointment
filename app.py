from flask import Flask, render_template, request, redirect
from config import get_connection

app = Flask(__name__)


# -----------------------
# 首頁：顯示醫師班表
# -----------------------
@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            d.name AS doctor_name, 
            s.work_date, 
            s.work_shift,
            ISNULL(a.count, 0) AS booked_count
        FROM Doctor_Schedules s
        JOIN Doctors d ON s.doctor_id = d.doctor_id
        LEFT JOIN (
            SELECT doctor_id, appt_date, work_shift, COUNT(*) AS count
            FROM Appointments
            WHERE status = 'Scheduled'
            GROUP BY doctor_id, appt_date, work_shift
        ) a
        ON s.doctor_id = a.doctor_id AND s.work_date = a.appt_date AND s.work_shift = a.work_shift
        ORDER BY s.work_date, s.work_shift
    """)

    schedule = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("index.html", schedule=schedule)



# -----------------------
# 查 patient_id（用身分證字號）
# -----------------------
def find_patient_id(identifier):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT patient_id FROM Patients WHERE identifier = ?", (identifier,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row.patient_id if row else None


# -----------------------
# 病人預約掛號
# -----------------------
@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    conn = get_connection()
    cursor = conn.cursor()

    # 取得所有醫生資料
    cursor.execute("SELECT doctor_id, name, specialty FROM Doctors")
    doctors = cursor.fetchall()

    if request.method == 'POST':
        identifier = request.form['identifier']  # 身分證字號
        doctor_id = request.form['doctor_id']
        appt_date = request.form['appt_date']
        work_shift = request.form['work_shift']
        symptoms = request.form['symptoms']

        # 取得 patient_id
        cursor.execute("SELECT patient_id FROM Patients WHERE identifier = ?", (identifier,))
        row = cursor.fetchone()
        if not row:
            return "查無病患，請先完成初診"
        patient_id = row.patient_id

        # 1️⃣ 檢查醫師該日期該班是否有排班
        cursor.execute("""
            SELECT 1 FROM Doctor_Schedules
            WHERE doctor_id = ? AND work_date = ? AND work_shift = ?
        """, (doctor_id, appt_date, work_shift))
        if not cursor.fetchone():
            return "醫師該時段無班，請選擇其他日期或醫師"

        # 2️⃣ 檢查病人同一天同時段是否已有預約
        cursor.execute("""
            SELECT 1 FROM Appointments
            WHERE patient_id = ? AND appt_date = ? AND work_shift = ? AND status = 'Booked'
        """, (patient_id, appt_date, work_shift))
        if cursor.fetchone():
            return "您在該時段已經有預約了"

        # 3️⃣ 檢查該時段已有多少人預約
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM Appointments
            WHERE doctor_id = ? AND appt_date = ? AND work_shift = ? AND status = 'Booked'
        """, (doctor_id, appt_date, work_shift))
        cnt = cursor.fetchone().cnt
        if cnt >= 14:
            return "該時段已滿，請選擇其他時段"

        # 4️⃣ 建立預約
        cursor.execute("""
            INSERT INTO Appointments (patient_id, doctor_id, appt_date, work_shift, symptoms, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'Booked', GETDATE())
        """, (patient_id, doctor_id, appt_date, work_shift, symptoms))
        conn.commit()

        cursor.close()
        conn.close()
        return "預約成功！"

    cursor.close()
    conn.close()
    return render_template('appointment.html', doctors=doctors)


# -----------------------
# 查詢自己的預約（用身分證字號）
# -----------------------
@app.route('/my_appointments', methods=['GET'])
def my_appointments():
    identifier = request.args.get('pid')

    if not identifier:
        return "請輸入身分證字號"

    patient_id = find_patient_id(identifier)
    if not patient_id:
        return "查無此病人"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.appt_id, d.name AS doctor_name, a.appt_date, a.work_shift, 
               a.symptoms, a.status
        FROM Appointments a
        JOIN Doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.appt_date DESC
    """, (patient_id,))

    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("my_appointments.html", appointments=appointments)


# -----------------------
# 初診新增病人
# -----------------------
@app.route('/new_patient', methods=['GET', 'POST'])
def new_patient():
    if request.method == 'POST':
        name = request.form['name']
        birth_date = request.form['birth_date']
        gender = request.form['gender']
        identifier = request.form['identifier']
        phone = request.form['phone']
        email = request.form.get('email')
        contact_address = request.form['contact_address']
        registered_address = request.form.get('registered_address')
        emergency_name = request.form.get('emergency_name')
        emergency_relation = request.form.get('emergency_relation')
        emergency_phone = request.form.get('emergency_phone')

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO Patients 
                (name, birth_date, gender, identifier, phone, email,
                 contact_address, registered_address,
                 emergency_name, emergency_relation, emergency_phone,
                 created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """

        cursor.execute(query, (
            name, birth_date, gender, identifier, phone, email,
            contact_address, registered_address,
            emergency_name, emergency_relation, emergency_phone
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return "初診資料已新增"

    return render_template("new_patient.html")


# -----------------------
# 取消預約
# -----------------------
@app.route('/cancel/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE Appointments SET status = 'Cancelled' WHERE appt_id = ?", appt_id)
        conn.commit()
        message = "取消預約成功！"
    except Exception as e:
        message = f"取消失敗: {str(e)}"
    finally:
        conn.close()

    return message


# -----------------------
# 修改預約
# -----------------------
@app.route('/appointment/<int:appointment_id>/edit', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_doctor_id = request.form['doctor_id']
        new_date = request.form['appt_date']
        new_shift = request.form['work_shift']

        update_query = """
            UPDATE Appointments
            SET doctor_id = ?, appt_date = ?, work_shift = ?
            WHERE appt_id = ?
        """
        cursor.execute(update_query, (new_doctor_id, new_date, new_shift, appointment_id))
        conn.commit()

        cursor.close()
        conn.close()

        return "預約已更新"

    cursor.execute("SELECT * FROM Appointments WHERE appt_id = ?", (appointment_id,))
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    if not data:
        return "找不到預約"

    return f"""
    <form method="POST">
        醫生 ID：<input name="doctor_id" value="{data.doctor_id}">
        <br>
        日期：<input name="appt_date" type="date" value="{data.appt_date}">
        <br>
        時段：
        <select name="work_shift">
            <option value="morning" {"selected" if data.work_shift=="morning" else ""}>早上</option>
            <option value="afternoon" {"selected" if data.work_shift=="afternoon" else ""}>下午</option>
            <option value="evening" {"selected" if data.work_shift=="evening" else ""}>晚上</option>
        </select>
        <br><br>
        <button type="submit">更新</button>
    </form>
    """


if __name__ == '__main__':
    app.run(debug=True)
