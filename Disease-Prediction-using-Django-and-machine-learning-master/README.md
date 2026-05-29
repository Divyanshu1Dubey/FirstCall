<div align="center">

<img src="templates/logox.png" alt="FirstCall Logo" width="220"/>

# FirstCall — AI-Powered Healthcare Platform

**PU Code Hackathon 2.0 · Team ERROR_505 · PIET · Health Tech**

[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Mistral AI](https://img.shields.io/badge/AI-Mistral%20%7C%20Groq%20%7C%20Gemini-5C6CFF)](https://mistral.ai)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **FirstCall** bridges the gap between patients and healthcare by combining ML-based disease prediction, real-time doctor-patient consultation, an AI assistant, and a live pharmacy finder — all in one Django app.

</div>

---

## Table of Contents

- [Demo](#demo)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Deploy to DigitalOcean](#deploy-to-digitalocean)
- [ML Model](#ml-model)
- [Team](#team)

---

## Demo

| Screen | Description |
|--------|-------------|
| 🏠 Home | Landing page with video background and role-based login |
| 🩺 Disease Checker | Select symptoms → ML model predicts disease + specialist |
| 💬 Consultation | Real-time doctor-patient chat with AJAX polling |
| 🤖 AI Assistant | Floating bot powered by Mistral / Groq / Gemini with smart fallback |
| 🗺️ Pharmacy Finder | Interactive Leaflet.js map showing which pharmacies stock your medicine |
| 💊 Alternative Drugs | Search any medicine to get safer substitutes |

---

## Features

### 🩺 ML Disease Prediction
- Trained Naive Bayes model on 132 symptoms → 41 diseases
- 94.8% reported accuracy
- Returns predicted disease, confidence score, and recommended specialist type
- Saves prediction to DB and links directly to doctor consultation flow

### 👨‍⚕️ Doctor–Patient Consultation
- Role-based accounts: Patient, Doctor, Admin
- Real-time chat via AJAX polling (2-second refresh)
- Patients rate and review doctors after consultation
- Full consultation history for both roles

### 🤖 FirstCall AI Assistant
- Floating chat widget available on every page
- Provider waterfall: **Mistral** → **Groq** → **Gemini** → smart local fallback
- Handles: symptom guidance, drug alternatives, pharmacy queries, doctor selection
- Fallback works with zero API keys — never shows a broken UI
- Quick-prompt chips for one-tap common questions

### 🗺️ Nearby Pharmacy Finder
- **No Google Maps redirect** — results stay on the page
- Interactive **Leaflet.js + OpenStreetMap** map (free, no API key)
- Green markers = pharmacies stocking your searched medicine
- Grey markers = other nearby pharmacies
- Click any marker for name, hours, phone, and stock list
- 8 demo pharmacies with real coordinates; drug badges highlight your search term

### 💊 Alternative Drugs
- Search any medicine name to get safer or equivalent substitutes
- Checks Django DB first, falls back to a curated local dictionary
- Covers: paracetamol, ibuprofen, amoxicillin, cetirizine, omeprazole, metformin, and more

### 🔐 Auth & Profiles
- Separate signup/login flows for patients and doctors
- Session-based authentication
- Profile pages with consultation history

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.0 (Python 3.11) |
| ML | scikit-learn 1.8 · joblib · Naive Bayes |
| AI APIs | Mistral AI · Groq (llama-3.3-70b) · Gemini 2.0 Flash |
| Frontend | Bootstrap 4 · jQuery · Font Awesome 5 |
| Maps | Leaflet.js 1.9 + OpenStreetMap (no API key needed) |
| Database | PostgreSQL (production) · SQLite (local dev) |
| Static files | WhiteNoise |
| Server | Gunicorn |
| Hosting | DigitalOcean App Platform |

---

## Project Structure

```
firstcall/
├── disease_prediction/       # Django project config
│   ├── settings.py           # Production-ready settings
│   ├── urls.py
│   └── wsgi.py
├── main_app/                 # Core app — views, models, ML
│   ├── views.py              # All views + AI providers + pharmacy logic
│   ├── models.py             # Patient, Doctor, DiseaseInfo, Consultation
│   └── urls.py
├── accounts/                 # Auth — signup, login, logout
├── chats/                    # Real-time chat + feedback models
├── templates/
│   ├── basic.html            # Base template + AI bot widget
│   ├── homepage/
│   ├── patient/
│   │   ├── nearby_pharmacy/  # Leaflet map pharmacy finder
│   │   ├── alternative_drugs/
│   │   ├── checkdisease/
│   │   └── patient_ui/
│   ├── doctor/
│   ├── consultation/
│   └── admin/
├── trained_model             # Serialised Naive Bayes model (joblib)
├── requirements.txt
├── Procfile                  # Gunicorn start command for DO
├── runtime.txt               # Python 3.11.9
└── .do/app.yaml              # DigitalOcean App Spec
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Git

### Steps

```bash
# 1. Clone
git clone https://github.com/Divyanshu1Dubey/FirstCall.git
cd FirstCall

# 2. Create and activate virtual environment
python -m venv env
# Windows:
env\Scripts\activate
# macOS/Linux:
source env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (see Environment Variables section)
# 5. Run migrations
python manage.py migrate

# 6. Create a superuser (optional)
python manage.py createsuperuser

# 7. Start the server
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

---

## Environment Variables

Create a `.env` file in the project root (same folder as `manage.py`):

```env
# Required in production — use a long random string
SECRET_KEY=your-secret-key-here

# Set to True only for local development
DEBUG=True

# AI providers — at least one recommended; app works without any (fallback mode)
MISTRAL_API_KEY=your-mistral-key
GROQ_API_KEY=your-groq-key
GEMINI_API_KEY=your-gemini-key

# Injected automatically by DigitalOcean when a Postgres DB is attached
# DATABASE_URL=postgres://...
```

The app works fully without any API keys — the AI assistant uses a built-in rule-based fallback that handles symptoms, drug alternatives, and pharmacy queries.

---

## Deploy to DigitalOcean

### One-click via App Spec

1. Fork / push this repo to your GitHub account
2. Go to [cloud.digitalocean.com/apps](https://cloud.digitalocean.com/apps) → **Create App**
3. Connect GitHub → select this repo → branch `main`
4. DigitalOcean detects the `Procfile` automatically
5. Add environment variables (see table below)
6. Add a **Dev Database** (free) or **PostgreSQL** cluster
7. Click **Deploy**

The build command runs automatically:
```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
```

### Required Environment Variables on DigitalOcean

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `${APP_DOMAIN}` |
| `DJANGO_SETTINGS_MODULE` | `disease_prediction.settings` |
| `MISTRAL_API_KEY` | Your Mistral key |
| `GROQ_API_KEY` | Your Groq key |
| `GEMINI_API_KEY` | Your Gemini key |
| `DATABASE_URL` | Auto-injected when you attach a Postgres DB |

### Source Directory

Set **Source Directory** to:
```
Disease-Prediction-using-Django-and-machine-learning-master
```

---

## ML Model

The trained model (`trained_model`) is a **Naive Bayes classifier** trained on a dataset of 132 symptoms mapped to 41 diseases.

| Metric | Value |
|--------|-------|
| Algorithm | Multinomial Naive Bayes |
| Input features | 132 binary symptom flags |
| Output classes | 41 diseases |
| Reported accuracy | 94.8% |
| Serialisation | joblib |

After prediction, the app maps the disease to a specialist type (Cardiologist, Dermatologist, Neurologist, etc.) and lets the patient book a consultation directly.

---

## Team

| Name | Role |
|------|------|
| **Divyanshu Dubey** | Full-stack development, ML integration, AI assistant, deployment |
| **Chandan Kumar** | Team Lead, backend architecture |
| **Gopal** | Frontend, templates, UI/UX |
| **Atharv Gehlot** | ML model training, data pipeline |

**Institute:** PIET  
**Event:** PU Code Hackathon 2.0  
**Category:** Health Tech  

---

<div align="center">
  <sub>Built with ❤️ by Team ERROR_505 · FirstCall © 2025</sub>
</div>
