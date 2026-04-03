# 🏥 MediAI — AI-Powered Disease Prediction System

**Complete Healthcare Intelligence Platform**  
Symptom analysis · Doctor matching · Hospital directory · Appointment booking · Live AI Chat

---

## 📁 Project Structure

```
mediai/
├── frontend/
│   └── index.html          ← Complete single-page frontend (self-contained)
├── backend/
│   ├── app.py              ← Flask REST API
│   └── requirements.txt    ← Python dependencies
├── README.md               ← This file
└── .env.example            ← Environment variables template
```

---

## 🚀 Quick Start (Local Development)

### Option A — Frontend Only (Zero Setup)
Just open `frontend/index.html` in any browser. Everything works offline except the Live AI Chat (needs an Anthropic API key passed via the browser).

### Option B — Full Stack

**1. Clone / Download the project**
```bash
git clone https://github.com/YOUR_USERNAME/mediai.git
cd mediai
```

**2. Backend Setup**
```bash
cd backend
python -m venv venv

# Activate:
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows

pip install -r requirements.txt
python app.py
# → Running on http://localhost:5000
```

**3. Frontend**
Open `frontend/index.html` directly in your browser — no build step needed.

---

## 🌐 Deployment Guide

### Deploy Frontend → Netlify (Free, Recommended)

1. Go to [netlify.com](https://netlify.com) → **Add new site → Deploy manually**
2. Drag & drop the **`frontend/`** folder
3. Your site is live instantly at `https://random-name.netlify.app`

**Custom domain:**
- Netlify Dashboard → Domain Settings → Add custom domain

---

### Deploy Backend → Railway (Free tier available)

```bash
# Install Railway CLI
npm install -g @railway/cli

cd backend
railway login
railway init
railway up
```
Railway auto-detects Python and uses `gunicorn` from `requirements.txt`.

**Or use Render.com (also free):**
1. New Web Service → Connect GitHub repo
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app`
4. Set environment variable `ANTHROPIC_API_KEY` in dashboard

---

### Deploy Frontend → Vercel

```bash
npm install -g vercel
cd frontend
vercel
# Follow prompts → deployed in 30 seconds
```

---

### Full Docker Deployment

**`docker-compose.yml`** (place in project root):
```yaml
version: '3.8'
services:
  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro

  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    restart: unless-stopped
```

**`backend/Dockerfile`**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

```bash
# Build and run
docker-compose up --build
```

---

### Deploy to AWS EC2

```bash
# On your EC2 instance (Ubuntu 22.04)
sudo apt update && sudo apt install -y python3-pip nginx

# Clone project
git clone https://github.com/YOUR_USERNAME/mediai.git
cd mediai/backend
pip3 install -r requirements.txt

# Run with gunicorn (production)
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app &

# Nginx config: /etc/nginx/sites-available/mediai
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
    }

    location / {
        root /home/ubuntu/mediai/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}

sudo ln -s /etc/nginx/sites-available/mediai /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 🔑 Environment Variables

Create `.env` in `backend/`:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
FLASK_ENV=production
SECRET_KEY=your-random-secret-key
```

---

## 📡 API Reference

### POST `/api/predict`
```json
{
  "symptoms": ["chest_pain", "shortness_breath", "sweating_sudden"],
  "age": 52,
  "sex": "male",
  "severity": 8,
  "duration": "few_hours"
}
```
**Response:**
```json
{
  "predictions": [
    {
      "name": "Heart Attack (Myocardial Infarction)",
      "confidence": 87,
      "specialist": "Cardiologist",
      "emergency": true,
      "precautions": ["Call 112 immediately", "..."],
      "icd": "I21"
    }
  ]
}
```

### GET `/api/symptoms`
Returns all 200+ symptoms with categories.

### GET `/api/hospitals?city=Mumbai`
Returns filtered hospital list.

### GET `/api/doctors?specialty=Cardiologist`
Returns specialists for given specialty.

### POST `/api/appointments`
```json
{
  "name": "Rahul Sharma",
  "phone": "9876543210",
  "doctor": "Dr. Devi Prasad Shetty",
  "hospital": "Narayana Health, Bangalore",
  "date": "2025-12-15",
  "time": "10:30 AM",
  "reason": "Chest pain and palpitations"
}
```

---

## 🛡️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML5, CSS3, JavaScript (ES6+) |
| Backend | Python 3.11 + Flask + Flask-CORS |
| AI Chat | Anthropic Claude API (claude-sonnet-4) |
| ML Engine | Rule-based Jaccard Similarity (upgradeable to scikit-learn RF) |
| Deployment | Netlify (FE) + Railway/Render (BE) |
| Container | Docker + Nginx |

---

## 🔬 Upgrading to Real ML (scikit-learn)

Replace the rule-based engine with a trained Random Forest:

```python
# train_model.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
import pandas as pd, joblib

# Load dataset (use Kaggle Disease-Symptom dataset)
df = pd.read_csv("disease_symptom_dataset.csv")
mlb = MultiLabelBinarizer()

X = mlb.fit_transform(df["symptoms"])
y = df["disease"]

clf = RandomForestClassifier(n_estimators=200, random_state=42)
clf.fit(X, y)

joblib.dump(clf, "model.pkl")
joblib.dump(mlb, "mlb.pkl")
```

```python
# In app.py — replace predict() with:
import joblib
clf = joblib.load("model.pkl")
mlb = joblib.load("mlb.pkl")

@app.route("/api/predict", methods=["POST"])
def predict():
    symptoms = request.json["symptoms"]
    X = mlb.transform([symptoms])
    probs = clf.predict_proba(X)[0]
    top = sorted(zip(clf.classes_, probs), key=lambda x: -x[1])[:5]
    return jsonify({"predictions": [{"name":c,"confidence":round(p*100)} for c,p in top]})
```

---

## ⚠️ Medical Disclaimer

MediAI is for **informational and educational purposes only**.  
It is NOT a substitute for professional medical advice, diagnosis, or treatment.  
Always consult a qualified healthcare provider.  
**Emergency India: 112 | NIMHANS Helpline: 080-46110007**

---

## 📄 License
MIT License — Free to use, modify, and distribute.

**Built with ❤️ for India's healthcare access challenge.**
