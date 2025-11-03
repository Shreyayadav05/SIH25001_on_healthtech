from flask import Flask, render_template, jsonify, request, send_file
import json, pickle, numpy as np, random, threading, io
from fpdf import FPDF
import time

app = Flask(__name__)

# Load DL model
model = pickle.load(open('models/disease_predictor.pkl','rb'))

# Sample data for 20 villages
with open('data/sample_data.json') as f:
    village_data = json.load(f)

recommendations = {
    "Cholera":"Boil water, chlorinate, maintain hygiene.",
    "Diarrhea":"Install water filters, promote handwashing.",
    "Typhoid":"Vaccination, improved sanitation required."
}

# Function to calculate Community Health Score
def calc_health_score(v):
    alert_score = {"High":3,"Medium":2,"Low":1}[v['level']]
    ph_score = max(0,10-abs(7-v['water_ph'])*3)
    turbidity_score = max(0,10-v['turbidity'])
    temp_score = max(0,10-abs(30-v['temperature']))
    humidity_score = max(0,10-abs(75-v['humidity'])/2)
    total = alert_score*5 + ph_score + turbidity_score + temp_score + humidity_score
    return round(total,2)

# Live IoT simulation for all villages
def simulate_data():
    while True:
        for v in village_data['villages']:
            v['water_ph'] = round(random.uniform(6.0,8.0),1)
            v['turbidity'] = random.randint(1,15)
            v['temperature'] = random.randint(25,35)
            v['humidity'] = random.randint(60,90)
            v['active_cases'] = random.randint(1,25)
            features = [v['water_ph'],v['turbidity'],v['temperature'],v['humidity']]
            v['disease_alert'] = model.predict(np.array(features).reshape(1,-1))[0]
            v['level'] = "High" if v['disease_alert']=="Cholera" else ("Medium" if v['disease_alert']=="Diarrhea" else "Low")
            v['health_score'] = calc_health_score(v)
        time.sleep(5)

threading.Thread(target=simulate_data,daemon=True).start()

@app.route('/')
def dashboard():
    return render_template('index.html', alerts=village_data)

@app.route('/api/alerts')
def api_alerts():
    return jsonify(village_data)

@app.route('/download-report/<village_name>')
def download_report(village_name):
    village = next((v for v in village_data['villages'] if v['name']==village_name),None)
    if not village: return "Not Found",404
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,f"{village_name} Health Report",0,1,"C")
    pdf.ln(5)
    pdf.set_font("Arial","",12)
    for k in ['water_ph','turbidity','temperature','humidity','active_cases','disease_alert','level','health_score']:
        pdf.cell(0,10,f"{k.replace('_',' ').title()}: {village[k]}",0,1)
    pdf.cell(0,10,f"Recommendation: {recommendations.get(village['disease_alert'],'Monitor')}",0,1)
    output=io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return send_file(output,download_name=f"{village_name}_report.pdf",as_attachment=True)

if __name__=="__main__":
    app.run(debug=True)

