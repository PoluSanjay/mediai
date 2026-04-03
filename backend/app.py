"""
MediAI — Flask Backend
AI-Powered Disease Prediction System
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json, random, string, datetime

app = Flask(__name__)
CORS(app)

# ── Appointment store (in-memory; swap for DB in production) ──
appointments = {}

def gen_ref():
    return "MEDAI-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ── Routes ─────────────────────────────────────────────────────

@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "MediAI Backend", "version": "1.0.0"})


@app.route("/api/symptoms", methods=["GET"])
def get_symptoms():
    """Return full symptoms list."""
    return jsonify({"symptoms": SYMPTOMS})


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Body: { symptoms: [str], age?: int, sex?: str, severity?: int, duration?: str }
    Returns ranked conditions with confidence scores.
    """
    data = request.get_json(force=True)
    user_syms = set(data.get("symptoms", []))
    severity  = int(data.get("severity", 5))

    if not user_syms:
        return jsonify({"error": "No symptoms provided"}), 400

    scored = []
    for key, cond in CONDITIONS.items():
        cond_syms = set(cond["symptoms"])
        matches   = user_syms & cond_syms
        if not matches:
            continue
        # Jaccard + coverage blended score
        union      = user_syms | cond_syms
        jaccard    = len(matches) / len(union)
        coverage   = len(matches) / len(cond_syms)
        confidence = round((jaccard * 0.4 + coverage * 0.6) * 100)
        if cond.get("emergency") and severity >= 7:
            confidence = min(int(confidence * 1.3), 95)
        if confidence < 10:
            continue
        scored.append({
            "key":        key,
            "name":       cond["name"],
            "emoji":      cond["emoji"],
            "severity":   cond["severity"],
            "confidence": confidence,
            "description": cond["description"],
            "specialist": cond["specialist"],
            "precautions": cond["precautions"],
            "tags":        cond["tags"],
            "emergency":   cond.get("emergency", False),
            "icd":         cond.get("icd", ""),
            "matches":     list(matches),
        })

    scored.sort(key=lambda x: x["confidence"], reverse=True)
    return jsonify({"predictions": scored[:5], "symptom_count": len(user_syms)})


@app.route("/api/doctors", methods=["GET"])
def get_doctors():
    """?specialty=Cardiologist"""
    spec = request.args.get("specialty", "")
    if spec and spec in DOCTORS:
        return jsonify({"doctors": DOCTORS[spec]})
    return jsonify({"doctors": DOCTORS})


@app.route("/api/hospitals", methods=["GET"])
def get_hospitals():
    """?city=Mumbai"""
    city = request.args.get("city", "")
    result = [h for h in HOSPITALS if not city or h["city"] == city]
    return jsonify({"hospitals": result})


@app.route("/api/appointments", methods=["POST"])
def book_appointment():
    """
    Body: { name, phone, doctor, hospital, date, time, reason }
    """
    d = request.get_json(force=True)
    required = ["name", "phone", "doctor", "hospital", "date", "time"]
    missing  = [f for f in required if not d.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    ref = gen_ref()
    appointments[ref] = {
        **d,
        "ref":    ref,
        "status": "confirmed",
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    return jsonify({"success": True, "reference": ref, "appointment": appointments[ref]})


@app.route("/api/appointments/<ref>", methods=["GET"])
def get_appointment(ref):
    appt = appointments.get(ref)
    if not appt:
        return jsonify({"error": "Appointment not found"}), 404
    return jsonify(appt)


@app.route("/api/appointments/<ref>", methods=["DELETE"])
def cancel_appointment(ref):
    if ref not in appointments:
        return jsonify({"error": "Not found"}), 404
    appointments[ref]["status"] = "cancelled"
    return jsonify({"success": True, "message": "Appointment cancelled"})


# ── Embedded Data ───────────────────────────────────────────────

SYMPTOMS = [
    {"id":"chest_pain","label":"Chest Pain / Tightness","cat":"Cardiac"},
    {"id":"heart_palpitations","label":"Heart Palpitations","cat":"Cardiac"},
    {"id":"shortness_breath","label":"Shortness of Breath","cat":"Respiratory"},
    {"id":"fever","label":"Fever","cat":"General"},
    {"id":"fatigue","label":"Fatigue / Tiredness","cat":"General"},
    {"id":"headache","label":"Headache","cat":"Neurological"},
    {"id":"nausea","label":"Nausea","cat":"Digestive"},
    {"id":"vomiting","label":"Vomiting","cat":"Digestive"},
    {"id":"cough","label":"Dry Cough","cat":"Respiratory"},
    {"id":"productive_cough","label":"Cough with Phlegm","cat":"Respiratory"},
    {"id":"abdominal_pain","label":"Abdominal Pain","cat":"Digestive"},
    {"id":"diarrhea","label":"Diarrhea","cat":"Digestive"},
    {"id":"painful_urination","label":"Painful Urination","cat":"Urological"},
    {"id":"blood_in_urine","label":"Blood in Urine","cat":"Urological"},
    {"id":"flank_pain","label":"Flank / Kidney Area Pain","cat":"Urological"},
    {"id":"joint_pain","label":"Joint Pain","cat":"Musculoskeletal"},
    {"id":"muscle_pain","label":"Muscle Pain","cat":"Musculoskeletal"},
    {"id":"rash","label":"Skin Rash","cat":"Dermatological"},
    {"id":"weight_loss","label":"Unexplained Weight Loss","cat":"General"},
    {"id":"excessive_thirst","label":"Excessive Thirst","cat":"Endocrine"},
    # … add all from JS SYMPTOMS_DB for full parity
]

CONDITIONS = {
    "heart_attack": {
        "name": "Heart Attack (Myocardial Infarction)", "emoji": "❤️‍🔥",
        "severity": "CRITICAL", "emergency": True,
        "description": "Blocked coronary artery causing heart muscle damage. Medical emergency.",
        "symptoms": ["chest_pain","chest_pressure","jaw_pain","sweating_sudden","shortness_breath","nausea","fatigue"],
        "specialist": "Cardiologist",
        "precautions": ["Call 112 immediately","Chew aspirin if not allergic","Rest and stay calm","Do not eat or drink"],
        "tags": ["Emergency","Cardiac","Life-Threatening"], "icd": "I21",
    },
    "kidney_stone": {
        "name": "Kidney Stone (Nephrolithiasis)", "emoji": "🪨",
        "severity": "HIGH", "emergency": False,
        "description": "Hard mineral deposits in kidney causing severe flank pain.",
        "symptoms": ["flank_pain","blood_in_urine","painful_urination","nausea","vomiting"],
        "specialist": "Urologist/Nephrologist",
        "precautions": ["Drink 2-3L water daily","Pain relievers","Strain urine","Low-oxalate diet"],
        "tags": ["Urological","Painful"], "icd": "N20",
    },
    "diabetes_type2": {
        "name": "Type 2 Diabetes Mellitus", "emoji": "🩸",
        "severity": "MODERATE", "emergency": False,
        "description": "Chronic condition with elevated blood glucose levels.",
        "symptoms": ["excessive_thirst","frequent_urination","excessive_hunger","fatigue","vision_changes","weight_loss"],
        "specialist": "Endocrinologist / Diabetologist",
        "precautions": ["Monitor blood glucose","Low-sugar diet","Exercise 150 min/week","HbA1c every 3 months"],
        "tags": ["Chronic","Endocrine"], "icd": "E11",
    },
    "pneumonia": {
        "name": "Pneumonia", "emoji": "🫁",
        "severity": "HIGH", "emergency": False,
        "description": "Lung infection causing cough, fever and breathing difficulty.",
        "symptoms": ["productive_cough","fever","chills","shortness_breath","fatigue"],
        "specialist": "Pulmonologist / Chest Physician",
        "precautions": ["Complete antibiotics","Rest and hydrate","Monitor SpO2","Avoid smoking"],
        "tags": ["Respiratory","Infectious"], "icd": "J18",
    },
}

DOCTORS = {
    "Cardiologist": [
        {"name":"Dr. Devi Prasad Shetty","spec":"Interventional Cardiologist","hospital":"Narayana Health, Bangalore","rating":5.0,"exp":"35+ years"},
        {"name":"Dr. Naresh Trehan","spec":"Cardiovascular Surgeon","hospital":"Medanta, Gurugram","rating":4.9,"exp":"40+ years"},
    ],
    "Urologist/Nephrologist": [
        {"name":"Dr. Anant Kumar","spec":"Kidney Transplant & Urology","hospital":"Medanta, Gurugram","rating":4.9,"exp":"30+ years"},
        {"name":"Dr. Mahesh Desai","spec":"Uro-oncology","hospital":"Muljibhai Patel Hospital, Nadiad","rating":4.8,"exp":"28+ years"},
    ],
}

HOSPITALS = [
    {"name":"AIIMS New Delhi","city":"Delhi","rank":1,"beds":2500,"rating":4.9,"type":"Government","specialties":["Cardiology","Neurology","Oncology","Transplant"]},
    {"name":"Apollo Hospitals","city":"Chennai","rank":2,"beds":10000,"rating":4.8,"type":"Private","specialties":["Cardiac Surgery","Transplant","Oncology"]},
    {"name":"Medanta - The Medicity","city":"Gurugram","rank":3,"beds":1250,"rating":4.9,"type":"Private","specialties":["Heart Surgery","Liver Transplant","Cancer"]},
    {"name":"Narayana Health","city":"Bangalore","rank":4,"beds":5000,"rating":4.8,"type":"Private","specialties":["Cardiac Surgery","Bone Marrow Transplant"]},
    {"name":"Kokilaben Hospital","city":"Mumbai","rank":5,"beds":750,"rating":4.8,"type":"Private","specialties":["Oncology","Orthopedics","Neurology"]},
    {"name":"Tata Memorial Hospital","city":"Mumbai","rank":6,"beds":629,"rating":4.9,"type":"Government","specialties":["Oncology","Radiation","Transplant"]},
    {"name":"Christian Medical College","city":"Vellore","rank":7,"beds":2700,"rating":4.9,"type":"Mission","specialties":["Hematology","Genetics","Transplant"]},
    {"name":"AIG Hospitals","city":"Hyderabad","rank":8,"beds":1000,"rating":4.9,"type":"Private","specialties":["Gastroenterology","Liver Transplant"]},
    {"name":"NIMHANS","city":"Bangalore","rank":9,"beds":2000,"rating":4.9,"type":"Government","specialties":["Psychiatry","Neurology","Neurosurgery"]},
    {"name":"Fortis Memorial Research","city":"Gurugram","rank":10,"beds":310,"rating":4.8,"type":"Private","specialties":["Cardiac Sciences","Robotics Surgery"]},
]

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
