from flask import Flask, render_template, request, redirect, session, url_for, send_file
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "smarthealth2025"

# ---------------- AUTO CREATE DATABASE FILES ----------------

if not os.path.exists("users.csv"):
    pd.DataFrame(columns=["username", "password", "role"]).to_csv("users.csv", index=False)

if not os.path.exists("symptoms.csv"):
    pd.DataFrame(columns=["name", "age", "symptom", "village"]).to_csv("symptoms.csv", index=False)

if not os.path.exists("sensor_data.csv"):
    pd.DataFrame(columns=["pH", "Turbidity", "Temperature", "TDS", "Outbreak"]).to_csv("sensor_data.csv", index=False)

if not os.path.exists("report_hashes.csv"):
    pd.DataFrame(columns=["report_id", "hash"]).to_csv("report_hashes.csv", index=False)

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = pd.read_csv("users.csv", dtype=str).fillna("")

        username = request.form.get("username")
        password = request.form.get("password")

        for i in range(len(users)):
            if users.loc[i, "username"] == username and users.loc[i, "password"] == password:
                session["user"] = username
                session["role"] = users.loc[i, "role"]
                return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid Login")

    return render_template("login.html")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    users = pd.read_csv("users.csv", dtype=str).fillna("")

    if request.method == "POST":
        users.loc[len(users)] = [
            request.form.get("username"),
            request.form.get("password"),
            request.form.get("role")
        ]
        users.to_csv("users.csv", index=False)
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    data = pd.read_csv("sensor_data.csv")
    return render_template("dashboard.html", tables=data.to_html(index=False))

# ---------------- SYMPTOMS REPORT ----------------

@app.route("/symptoms", methods=["GET", "POST"])
def symptoms():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        df = pd.read_csv("symptoms.csv", dtype=str)

        df.loc[len(df)] = [
            request.form.get("name"),
            request.form.get("age"),
            request.form.get("symptom"),
            request.form.get("village")
        ]

        df.to_csv("symptoms.csv", index=False)
        return redirect(url_for("dashboard"))

    return render_template("symptoms.html")

# ---------------- REPORTED CASES + SEARCH ----------------

@app.route("/reported-cases", methods=["GET", "POST"])
def reported_cases():
    if "user" not in session:
        return redirect(url_for("login"))

    df = pd.read_csv("symptoms.csv", dtype=str).fillna("")
    query = request.form.get("search")

    if query:
        query = query.lower()
        df = df[
            df["name"].str.lower().str.contains(query) |
            df["age"].str.lower().str.contains(query) |
            df["symptom"].str.lower().str.contains(query) |
            df["village"].str.lower().str.contains(query)
        ]

    return render_template("reported_cases.html", tables=df.to_html(index=False), search=query)

# ---------------- EXPORT EXCEL ----------------

@app.route("/export-excel")
def export_excel():
    df = pd.read_csv("symptoms.csv")
    df.to_excel("reports.xlsx", index=False)
    return send_file("reports.xlsx", as_attachment=True)

# ---------------- EXPORT PDF + QR + HASH ----------------

@app.route("/export-pdf")
def export_pdf():
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from datetime import datetime
    import qrcode, uuid, hashlib, json

    df = pd.read_csv("symptoms.csv", dtype=str).fillna("")

    report_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    report_id = "RPT-" + str(uuid.uuid4())[:8].upper()

    raw_data = json.dumps(df.to_dict(), sort_keys=True) + report_id + report_date
    report_hash = hashlib.sha256(raw_data.encode()).hexdigest()

    hash_df = pd.read_csv("report_hashes.csv")
    hash_df.loc[len(hash_df)] = [report_id, report_hash]
    hash_df.to_csv("report_hashes.csv", index=False)

    verify_url = f"http://127.0.0.1:5000/verify/{report_id}"
    qr_path = "static/qr_verify.png"
    qrcode.make(verify_url).save(qr_path)

    pdf = SimpleDocTemplate("government_verified_health_report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()

    header = Paragraph(
        f"<b>Smart Community Health Monitoring Report</b><br/>"
        f"Report ID: {report_id}<br/>"
        f"Generated On: {report_date}<br/>"
        f"Blockchain Hash: {report_hash[:24]}...",
        styles["Title"]
    )

    data = [list(df.columns)] + df.values.tolist()

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))

    qr_img = Image(qr_path, width=1.5 * inch, height=1.5 * inch)

    verified_note = Paragraph(
        "<b>QR Verified Government Record</b><br/>Scan QR to verify authenticity online.",
        styles["Normal"]
    )

    pdf.build([header, table, verified_note, qr_img])

    return send_file("government_verified_health_report.pdf", as_attachment=True)

# ---------------- QR VERIFICATION PAGE ----------------

@app.route("/verify/<report_id>")
def verify_report(report_id):
    df = pd.read_csv("report_hashes.csv", dtype=str)

    if report_id in df["report_id"].values:
        status = "✅ AUTHENTIC REPORT — Blockchain Hash Verified"
    else:
        status = "❌ FAKE REPORT DETECTED — INVALID HASH"

    return render_template("verify.html", report_id=report_id, status=status)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- SERVER ----------------

if __name__ == "__main__":
    print("✅ Smart Health Government Server Running...")
    app.run(debug=True)
