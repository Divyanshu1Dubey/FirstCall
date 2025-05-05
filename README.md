<!-- Banner -->
<p align="center">
  <img src="https://img.shields.io/badge/AI%20HealthTech-FIRST__CALL-00b894?style=for-the-badge&logo=python&logoColor=white">
</p>

<h1 align="center">🩺 FIRST_CALL – AI-Powered Healthcare Assistant</h1>

<p align="center">
  A next-gen healthcare platform that predicts diseases, recommends medicines, tracks real-time pharmacy availability, and connects patients with doctors — all powered by <b>AI, Django, and Geolocation APIs</b>.
</p>

<p align="center">
  <a href="https://drive.google.com/file/d/1gUoyNtWCDOh9wYnXFoEgbdO65UYro0NX/view?usp=sharing"><img src="https://img.shields.io/badge/Watch-Demo%20Video-red?style=for-the-badge&logo=youtube"></a>
  <a href="https://github.com/Divyanshu1Dubey/FIRST_CALL"><img src="https://img.shields.io/github/stars/Divyanshu1Dubey/FIRST_CALL?style=for-the-badge&color=yellow&logo=github"></a>
</p>

---

## ✨ Features

🚑 **Symptom-Based Disease Prediction**  
- Uses ML models (Decision Tree, Random Forest, Naive Bayes) trained on real datasets.  
- Accuracy: **94.8%**

💊 **Drug Information & Alternative Suggestions**  
- Pulls data from APIs to show dosage, interactions, and safer alternatives.

📍 **Nearby Pharmacies (via Streamlit)**  
- Integrated with **geolocation** to find and show pharmacies with the required drugs on a map.

📚 **Health History Analysis**  
- Upload your records (PDF) and get AI-driven preventive healthcare suggestions.

💬 **Doctor–Patient Chat System**  
- Role-based access for doctors and patients with a built-in messaging interface.

🧪 **Admin Dashboard**  
- Manage users, doctors, predictions, and medical logs in a secure interface.

---

## 📷 Screenshots

| Symptom Checker | Pharmacy Map | Doctor Chat |
|:---------------:|:------------:|:-----------:|
| ![Symptom](https://i.imgur.com/bXv4Wce.png) | ![Pharmacy](https://i.imgur.com/ih3X8LZ.png) | ![Chat](https://i.imgur.com/qfMaqNU.png) |

---

## 🧠 Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Frontend   | HTML, CSS, JS, Bootstrap          |
| Backend    | Django (Python)                   |
| Database   | PostgreSQL                        |
| Visualization | Streamlit                      |
| AI Models  | Decision Tree, Random Forest, Naive Bayes |
| Others     | Geolocation API, Orange Tool      |

---

## 🛠 Setup Instructions

### 🔗 Prerequisites
- Python 3.8+
- PostgreSQL + PgAdmin
- Virtual environment (recommended)

### ⚙️ Installation

```bash
# Clone the project
git clone https://github.com/Divyanshu1Dubey/FIRST_CALL
cd FIRST_CALL

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database Setup
# Create a PostgreSQL DB instance named "predico" via PgAdmin

# Migrations


python manage.py makemigrations
python manage.py migrate

# Run the server
python manage.py runserver
Visit: http://127.0.0.1:8000/

## 📂 Dataset

- **Source**: [Kaggle – Disease Prediction Dataset](https://www.kaggle.com/neelima98/disease-prediction-using-machine-learning)
- 132 Symptoms across 40 diseases
- Combines structured and unstructured hospital data

### 📊 Models Used

- Decision Tree  
- Naive Bayes  
- Random Forest  

🚀 **Achieved Accuracy**: **94.8%**

---

## 🧾 Application Workflow

```mermaid
graph TD;
    A[User Inputs Symptoms] --> B[AI/ML Model Predicts Disease];
    B --> C[Suggest Medication];
    C --> D[Search Nearby Pharmacies];
    B --> E[Connect to Doctors via Chat];
    F[Upload Health History] --> G[Preventive Health Risk Analysis];
