from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
import os
import re
import requests
from datetime import date

from django.contrib import messages
from django.contrib.auth.models import User , auth
from .models import patient , doctor , diseaseinfo , consultation ,rating_review
from chats.models import Chat,Feedback
from .models import Drug, AlternativeDrug


# Create your views here.


#loading trained_model
import joblib as jb
model = jb.load('trained_model')


LOCAL_DRUG_ALTERNATIVES = {
  'paracetamol': ['Acetaminophen (same active ingredient in many brands)', 'Ibuprofen for some pain/fever use cases', 'Aspirin if appropriate for the person and not contraindicated'],
  'acetaminophen': ['Paracetamol (same active ingredient)', 'Ibuprofen for some pain/fever use cases', 'Aspirin if appropriate for the person and not contraindicated'],
  'ibuprofen': ['Paracetamol/acetaminophen', 'Naproxen in some cases', 'Topical pain relief options for localized pain'],
  'amoxicillin': ['Amoxicillin-clavulanate only when prescribed', 'Azithromycin when clinically appropriate', 'Cephalexin in some infections if recommended by a doctor'],
  'cetirizine': ['Loratadine', 'Fexofenadine', 'Levocetirizine'],
  'omeprazole': ['Pantoprazole', 'Esomeprazole', 'Famotidine'],
  'metformin': ['Extended-release metformin', 'Lifestyle measures as advised by a clinician', 'Alternative diabetes medicines only under doctor guidance'],
  'paroxetine': ['Sertraline', 'Escitalopram', 'Fluoxetine']
}

LOCAL_PHARMACIES = [
  {
    'name': 'City Care Pharmacy',
    'area': 'Central Market',
    'phone': '+91-90000-11111',
    'hours': '8:00 AM - 10:00 PM',
    'medicines': ['paracetamol', 'ibuprofen', 'cetirizine', 'omeprazole', 'aspirin'],
    'lat': 30.7333,
    'lng': 76.7794,
  },
  {
    'name': 'HealthHub Medical Store',
    'area': 'Railway Road',
    'phone': '+91-90000-22222',
    'hours': '24 Hours',
    'medicines': ['paracetamol', 'amoxicillin', 'metformin', 'levocetirizine', 'azithromycin'],
    'lat': 30.7350,
    'lng': 76.7850,
  },
  {
    'name': 'WellLife Pharmacy',
    'area': 'Civil Lines',
    'phone': '+91-90000-33333',
    'hours': '9:00 AM - 9:00 PM',
    'medicines': ['ibuprofen', 'cetirizine', 'pantoprazole', 'aspirin', 'naproxen'],
    'lat': 30.7310,
    'lng': 76.7760,
  },
  {
    'name': 'FirstAid Chemist',
    'area': 'Bus Stand',
    'phone': '+91-90000-44444',
    'hours': '7:30 AM - 11:00 PM',
    'medicines': ['paracetamol', 'omeprazole', 'fexofenadine', 'metformin', 'cetirizine'],
    'lat': 30.7290,
    'lng': 76.7820,
  },
  {
    'name': 'MediPlus Pharmacy',
    'area': 'Sector 17',
    'phone': '+91-90000-55555',
    'hours': '8:00 AM - 11:00 PM',
    'medicines': ['paracetamol', 'ibuprofen', 'amoxicillin', 'cetirizine', 'omeprazole', 'metformin'],
    'lat': 30.7400,
    'lng': 76.7900,
  },
  {
    'name': 'Apollo Pharmacy',
    'area': 'Sector 22',
    'phone': '+91-90000-66666',
    'hours': '24 Hours',
    'medicines': ['paracetamol', 'ibuprofen', 'aspirin', 'azithromycin', 'pantoprazole', 'levocetirizine'],
    'lat': 30.7270,
    'lng': 76.7700,
  },
  {
    'name': 'Green Cross Medical',
    'area': 'Model Town',
    'phone': '+91-90000-77777',
    'hours': '9:00 AM - 10:00 PM',
    'medicines': ['cetirizine', 'fexofenadine', 'naproxen', 'omeprazole', 'metformin'],
    'lat': 30.7380,
    'lng': 76.7730,
  },
  {
    'name': 'Sunrise Chemist',
    'area': 'Industrial Area',
    'phone': '+91-90000-88888',
    'hours': '8:30 AM - 9:30 PM',
    'medicines': ['paracetamol', 'aspirin', 'amoxicillin', 'ibuprofen', 'pantoprazole'],
    'lat': 30.7240,
    'lng': 76.7870,
  },
]


def _normalize_drug_name(value):
  return (value or '').strip().lower()


def _drug_alternatives_for_query(query):
  normalized = _normalize_drug_name(query)
  if not normalized:
    return None, []

  drug_obj = Drug.objects.filter(name__iexact=query).first()
  if drug_obj:
    alternatives = list(drug_obj.alternatives.values_list('alternative_name', flat=True))
    return drug_obj.name, alternatives

  for key, alternatives in LOCAL_DRUG_ALTERNATIVES.items():
    if key in normalized:
      return key.title(), alternatives

  return None, []


def _build_ai_system_prompt():
  return (
    "You are FirstCall AI, a concise healthcare assistant for a Django healthcare app. "
    "Help with symptom-based disease guidance, drug information, alternative medicines, "
    "doctor selection, and general health education. Keep answers short, practical, and "
    "supportive. Never claim to diagnose with certainty. Always recommend medical care "
    "for emergencies, severe symptoms, chest pain, trouble breathing, loss of consciousness, "
    "or rapidly worsening conditions. If the user asks for a medication or dosage, answer at a "
    "high level and remind them to confirm with a qualified clinician or pharmacist."
  )


def _fallback_ai_response(message):
  """Rule-based fallback used when all AI providers fail."""
  text = message.lower().strip()

  # Emergency keywords
  if any(w in text for w in ["chest pain", "can't breathe", "cannot breathe", "faint", "unconscious", "emergency", "heart attack"]):
    return (
      "This sounds urgent. Please call emergency services (112 / 911) or go to the nearest hospital immediately. "
      "Do not wait — get in-person medical help right away."
    )

  # Drug alternative patterns — broad matching
  alt_patterns = [
    r"(?:alternate|alternative|substitute|replace|instead of|other than|swap)\s+(?:of\s+|for\s+|to\s+)?([a-z0-9\- ]{3,30})",
    r"([a-z0-9\- ]{3,30})\s+(?:alternative|substitute|replacement|alternate)",
    r"what\s+(?:can\s+i\s+take|should\s+i\s+take)\s+instead\s+of\s+([a-z0-9\- ]{3,30})",
  ]
  for pattern in alt_patterns:
    m = re.search(pattern, text)
    if m:
      query = m.group(1).strip().rstrip('?.,')
      # Try each word in the query against our dict
      for word in query.split():
        for key in LOCAL_DRUG_ALTERNATIVES:
          if key in word or word in key:
            alts = LOCAL_DRUG_ALTERNATIVES[key]
            formatted = '\n'.join(f'  • {a}' for a in alts[:4])
            return (
              f"Common alternatives for {key.title()} (discuss with your pharmacist or doctor before switching):\n"
              f"{formatted}\n\n"
              f"Always check the active ingredient, dosage, and any allergies before changing medicines."
            )
      # Try the full query
      drug_name, alternatives = _drug_alternatives_for_query(query)
      if alternatives:
        formatted = '\n'.join(f'  • {a}' for a in alternatives[:4])
        return (
          f"Alternatives for {drug_name} to discuss with a clinician or pharmacist:\n"
          f"{formatted}"
        )

  # Direct drug name in message
  for key in LOCAL_DRUG_ALTERNATIVES:
    if key in text:
      alts = LOCAL_DRUG_ALTERNATIVES[key]
      formatted = '\n'.join(f'  • {a}' for a in alts[:4])
      return (
        f"Common alternatives for {key.title()}:\n"
        f"{formatted}\n\n"
        f"Confirm the right choice with a pharmacist or doctor based on your specific condition."
      )

  # Symptom guidance
  symptom_words = ["symptom", "fever", "cough", "cold", "pain", "rash", "headache", "vomit",
                   "nausea", "diarrhea", "dizziness", "fatigue", "tired", "sore throat", "breathless"]
  if any(w in text for w in symptom_words):
    return (
      "To get the best suggestion:\n"
      "  1. List your top 3 symptoms\n"
      "  2. Mention how many days they have lasted\n"
      "  3. Include your age and any fever temperature\n\n"
      "Then use the Check Disease tool for a model-based prediction, and follow up with a doctor."
    )

  # Pharmacy / medicine general
  if any(w in text for w in ["pharmacy", "chemist", "medical store", "where to buy", "available"]):
    return (
      "Use the Nearby Pharmacy Finder on your profile page to search which local pharmacies "
      "have your medicine in stock. Type the medicine name and your area to see results on the map."
    )

  # General medicine question
  if any(w in text for w in ["drug", "medicine", "tablet", "pill", "dose", "medication", "capsule"]):
    return (
      "For any medicine question:\n"
      "  • Use Alternative Drugs to find substitutes\n"
      "  • Use Nearby Pharmacy to check local stock\n"
      "  • Always confirm dosage and interactions with a pharmacist or doctor\n\n"
      "What specific medicine are you asking about?"
    )

  # Doctor / consultation
  if any(w in text for w in ["doctor", "specialist", "consult", "appointment", "clinic"]):
    return (
      "After running the disease checker, you can consult a specialist directly from the app. "
      "The system recommends the right type of doctor based on your predicted condition."
    )

  return (
    "I can help with:\n"
    "  • Symptom guidance — describe what you feel\n"
    "  • Drug alternatives — ask 'alternative of paracetamol'\n"
    "  • Nearby pharmacy — which store has your medicine\n"
    "  • Doctor selection — after checking your disease\n\n"
    "What would you like help with?"
  )


def _call_mistral(message):
  """Call Mistral AI API."""
  api_key = os.getenv('MISTRAL_API_KEY')
  if not api_key:
    return None

  url = 'https://api.mistral.ai/v1/chat/completions'
  payload = {
    "model": "mistral-small-latest",
    "messages": [
      {"role": "system", "content": _build_ai_system_prompt()},
      {"role": "user", "content": message},
    ],
    "temperature": 0.4,
    "max_tokens": 350,
  }
  headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
  }
  response = requests.post(url, json=payload, headers=headers, timeout=20)
  response.raise_for_status()
  data = response.json()
  choices = data.get('choices', [])
  if choices:
    text = choices[0].get('message', {}).get('content', '').strip()
    if text:
      return text
  return None


def _call_groq(message):
  """Call Groq API with current supported model."""
  api_key = os.getenv('GROQ_API_KEY')
  if not api_key:
    return None

  url = 'https://api.groq.com/openai/v1/chat/completions'
  payload = {
    "model": "llama-3.3-70b-versatile",   # updated — llama-3.1-70b was decommissioned
    "messages": [
      {"role": "system", "content": _build_ai_system_prompt()},
      {"role": "user", "content": message},
    ],
    "temperature": 0.4,
    "max_tokens": 350,
  }
  headers = {"Authorization": f"Bearer {api_key}"}
  response = requests.post(url, json=payload, headers=headers, timeout=20)
  response.raise_for_status()
  data = response.json()
  choices = data.get('choices', [])
  if choices:
    text = choices[0].get('message', {}).get('content', '').strip()
    if text:
      return text
  return None


def _call_gemini(message):
  """Call Gemini API."""
  api_key = os.getenv('GEMINI_API_KEY')
  if not api_key:
    return None

  url = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.0-flash:generateContent?key={api_key}"
  )
  payload = {
    "contents": [
      {
        "role": "user",
        "parts": [{"text": _build_ai_system_prompt() + "\n\nUser message: " + message}],
      }
    ],
    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 350},
  }
  response = requests.post(url, json=payload, timeout=20)
  response.raise_for_status()
  data = response.json()
  candidates = data.get('candidates', [])
  if candidates:
    parts = candidates[0].get('content', {}).get('parts', [])
    text = ''.join(p.get('text', '') for p in parts).strip()
    if text:
      return text
  return None


def ai_assistant(request):
  if request.method != 'GET':
    return JsonResponse({'error': 'Only GET requests are supported.'}, status=405)

  message = request.GET.get('message', '').strip()
  if not message:
    return JsonResponse({'error': 'Missing message parameter.'}, status=400)

  # Priority order: Mistral (working) → Groq → Gemini → fallback
  providers = []
  if os.getenv('MISTRAL_API_KEY'):
    providers.append(('mistral', _call_mistral))
  if os.getenv('GROQ_API_KEY'):
    providers.append(('groq', _call_groq))
  if os.getenv('GEMINI_API_KEY'):
    providers.append(('gemini', _call_gemini))

  for provider_name, provider_fn in providers:
    try:
      reply = provider_fn(message)
      if reply:
        return JsonResponse({'reply': reply, 'provider': provider_name})
    except Exception:
      continue

  return JsonResponse({'reply': _fallback_ai_response(message), 'provider': 'fallback'})


def nearby_pharmacy(request):
  import json as _json
  if request.method != 'GET':
    return redirect('patient_ui')

  drug_query = request.GET.get('drug', '').strip()
  area_query = request.GET.get('area', '').strip()
  normalized_drug = _normalize_drug_name(drug_query)
  pharmacy_results = []

  for pharmacy in LOCAL_PHARMACIES:
    stock_match = True
    if normalized_drug:
      stock_match = any(
        normalized_drug in med or med in normalized_drug
        for med in pharmacy['medicines']
      )

    area_match = True
    if area_query:
      area_match = (
        area_query.lower() in pharmacy['area'].lower()
        or area_query.lower() in pharmacy['name'].lower()
      )

    if stock_match and area_match:
      pharmacy_results.append(pharmacy)

  # If area filter gave no results, fall back to drug-only match
  if not pharmacy_results and drug_query:
    for pharmacy in LOCAL_PHARMACIES:
      if any(normalized_drug in med or med in normalized_drug for med in pharmacy['medicines']):
        pharmacy_results.append(pharmacy)

  # All pharmacies for the map (shown as grey markers when no search)
  all_pharmacies_json = _json.dumps(LOCAL_PHARMACIES)
  results_json = _json.dumps(pharmacy_results)

  return render(
    request,
    'patient/nearby_pharmacy/index.html',
    {
      'drug_query': drug_query,
      'area_query': area_query,
      'pharmacies': pharmacy_results,
      'has_results': bool(pharmacy_results),
      'suggested_drugs': ['paracetamol', 'ibuprofen', 'cetirizine', 'omeprazole', 'amoxicillin', 'metformin'],
      'all_pharmacies_json': all_pharmacies_json,
      'results_json': results_json,
    }
  )


def alternative_drugs_page(request):
  if request.method != 'GET':
    return redirect('patient_ui')

  query = request.GET.get('drug', '').strip()
  drug_name, alternatives = _drug_alternatives_for_query(query)

  if query and not alternatives:
    drug_name = query

  return render(
    request,
    'patient/alternative_drugs/index.html',
    {
      'query': query,
      'drug_name': drug_name,
      'alternatives': alternatives,
      'has_results': bool(alternatives),
      'suggested_queries': ['paracetamol', 'ibuprofen', 'cetirizine', 'omeprazole']
    }
  )




def home(request):

  if request.method == 'GET':
        
      if request.user.is_authenticated:
        return render(request,'homepage/index.html')

      else :
        return render(request,'homepage/index.html')


def about(request):
    return render(request, 'about.html')
   
def contact(request):
    return render(request, 'contact.html')
       


def admin_ui(request):

    if request.method == 'GET':

      if request.user.is_authenticated:

        auser = request.user
        Feedbackobj = Feedback.objects.all()

        return render(request,'admin/admin_ui/admin_ui.html' , {"auser":auser,"Feedback":Feedbackobj})

      else :
        return redirect('home')



    if request.method == 'POST':

       return render(request,'patient/patient_ui/profile.html')





def patient_ui(request):

    if request.method == 'GET':

      if request.user.is_authenticated:

        patientusername = request.session['patientusername']
        puser = User.objects.get(username=patientusername)

        return render(request,'patient/patient_ui/profile.html' , {"puser":puser})

      else :
        return redirect('home')



    if request.method == 'POST':

       return render(request,'patient/patient_ui/profile.html')

       


def pviewprofile(request, patientusername):

    if request.method == 'GET':

          puser = User.objects.get(username=patientusername)

          return render(request,'patient/view_profile/view_profile.html', {"puser":puser})




def checkdisease(request):

  diseaselist=['Fungal infection','Allergy','GERD','Chronic cholestasis','Drug Reaction','Peptic ulcer diseae','AIDS','Diabetes ',
  'Gastroenteritis','Bronchial Asthma','Hypertension ','Migraine','Cervical spondylosis','Paralysis (brain hemorrhage)',
  'Jaundice','Malaria','Chicken pox','Dengue','Typhoid','hepatitis A', 'Hepatitis B', 'Hepatitis C', 'Hepatitis D',
  'Hepatitis E', 'Alcoholic hepatitis','Tuberculosis', 'Common Cold', 'Pneumonia', 'Dimorphic hemmorhoids(piles)',
  'Heart attack', 'Varicose veins','Hypothyroidism', 'Hyperthyroidism', 'Hypoglycemia', 'Osteoarthristis',
  'Arthritis', '(vertigo) Paroymsal  Positional Vertigo','Acne', 'Urinary tract infection', 'Psoriasis', 'Impetigo']


  symptomslist=['itching','skin_rash','nodal_skin_eruptions','continuous_sneezing','shivering','chills','joint_pain',
  'stomach_pain','acidity','ulcers_on_tongue','muscle_wasting','vomiting','burning_micturition','spotting_ urination',
  'fatigue','weight_gain','anxiety','cold_hands_and_feets','mood_swings','weight_loss','restlessness','lethargy',
  'patches_in_throat','irregular_sugar_level','cough','high_fever','sunken_eyes','breathlessness','sweating',
  'dehydration','indigestion','headache','yellowish_skin','dark_urine','nausea','loss_of_appetite','pain_behind_the_eyes',
  'back_pain','constipation','abdominal_pain','diarrhoea','mild_fever','yellow_urine',
  'yellowing_of_eyes','acute_liver_failure','fluid_overload','swelling_of_stomach',
  'swelled_lymph_nodes','malaise','blurred_and_distorted_vision','phlegm','throat_irritation',
  'redness_of_eyes','sinus_pressure','runny_nose','congestion','chest_pain','weakness_in_limbs',
  'fast_heart_rate','pain_during_bowel_movements','pain_in_anal_region','bloody_stool',
  'irritation_in_anus','neck_pain','dizziness','cramps','bruising','obesity','swollen_legs',
  'swollen_blood_vessels','puffy_face_and_eyes','enlarged_thyroid','brittle_nails',
  'swollen_extremeties','excessive_hunger','extra_marital_contacts','drying_and_tingling_lips',
  'slurred_speech','knee_pain','hip_joint_pain','muscle_weakness','stiff_neck','swelling_joints',
  'movement_stiffness','spinning_movements','loss_of_balance','unsteadiness',
  'weakness_of_one_body_side','loss_of_smell','bladder_discomfort','foul_smell_of urine',
  'continuous_feel_of_urine','passage_of_gases','internal_itching','toxic_look_(typhos)',
  'depression','irritability','muscle_pain','altered_sensorium','red_spots_over_body','belly_pain',
  'abnormal_menstruation','dischromic _patches','watering_from_eyes','increased_appetite','polyuria','family_history','mucoid_sputum',
  'rusty_sputum','lack_of_concentration','visual_disturbances','receiving_blood_transfusion',
  'receiving_unsterile_injections','coma','stomach_bleeding','distention_of_abdomen',
  'history_of_alcohol_consumption','fluid_overload','blood_in_sputum','prominent_veins_on_calf',
  'palpitations','painful_walking','pus_filled_pimples','blackheads','scurring','skin_peeling',
  'silver_like_dusting','small_dents_in_nails','inflammatory_nails','blister','red_sore_around_nose',
  'yellow_crust_ooze']

  alphabaticsymptomslist = sorted(symptomslist)

  


  if request.method == 'GET':
    
     return render(request,'patient/checkdisease/checkdisease.html', {"list2":alphabaticsymptomslist})




  elif request.method == 'POST':
       
      ## access you data by playing around with the request.POST object
      
      inputno = int(request.POST["noofsym"])
      print(inputno)
      if (inputno == 0 ) :
          return JsonResponse({'predicteddisease': "none",'confidencescore': 0 })
  
      else :

        psymptoms = []
        psymptoms = request.POST.getlist("symptoms[]")
       
        print(psymptoms)

      
        """      #main code start from here...
        """
      

      
        testingsymptoms = []
        #append zero in all coloumn fields...
        for x in range(0, len(symptomslist)):
          testingsymptoms.append(0)


        #update 1 where symptoms gets matched...
        for k in range(0, len(symptomslist)):

          for z in psymptoms:
              if (z == symptomslist[k]):
                  testingsymptoms[k] = 1


        inputtest = [testingsymptoms]

        print(inputtest)
      

        predicted = model.predict(inputtest)
        print("predicted disease is : ")
        print(predicted)

        y_pred_2 = model.predict_proba(inputtest)
        confidencescore=y_pred_2.max() * 100
        print(" confidence score of : = {0} ".format(confidencescore))

        confidencescore = format(confidencescore, '.0f')
        predicted_disease = predicted[0]

        

        #consult_doctor codes----------

        #   doctor_specialization = ["Rheumatologist","Cardiologist","ENT specialist","Orthopedist","Neurologist",
        #                             "Allergist/Immunologist","Urologist","Dermatologist","Gastroenterologist"]
        

        Rheumatologist = [  'Osteoarthristis','Arthritis']
       
        Cardiologist = [ 'Heart attack','Bronchial Asthma','Hypertension ']
       
        ENT_specialist = ['(vertigo) Paroymsal  Positional Vertigo','Hypothyroidism' ]

        Orthopedist = []

        Neurologist = ['Varicose veins','Paralysis (brain hemorrhage)','Migraine','Cervical spondylosis']

        Allergist_Immunologist = ['Allergy','Pneumonia',
        'AIDS','Common Cold','Tuberculosis','Malaria','Dengue','Typhoid']

        Urologist = [ 'Urinary tract infection',
         'Dimorphic hemmorhoids(piles)']

        Dermatologist = [  'Acne','Chicken pox','Fungal infection','Psoriasis','Impetigo']

        Gastroenterologist = ['Peptic ulcer diseae', 'GERD','Chronic cholestasis','Drug Reaction','Gastroenteritis','Hepatitis E',
        'Alcoholic hepatitis','Jaundice','hepatitis A',
         'Hepatitis B', 'Hepatitis C', 'Hepatitis D','Diabetes ','Hypoglycemia']
         
        if predicted_disease in Rheumatologist :
           consultdoctor = "Rheumatologist"
           
        if predicted_disease in Cardiologist :
           consultdoctor = "Cardiologist"
           

        elif predicted_disease in ENT_specialist :
           consultdoctor = "ENT specialist"
     
        elif predicted_disease in Orthopedist :
           consultdoctor = "Orthopedist"
     
        elif predicted_disease in Neurologist :
           consultdoctor = "Neurologist"
     
        elif predicted_disease in Allergist_Immunologist :
           consultdoctor = "Allergist/Immunologist"
     
        elif predicted_disease in Urologist :
           consultdoctor = "Urologist"
     
        elif predicted_disease in Dermatologist :
           consultdoctor = "Dermatologist"
     
        elif predicted_disease in Gastroenterologist :
           consultdoctor = "Gastroenterologist"
     
        else :
           consultdoctor = "other"


        request.session['doctortype'] = consultdoctor 

        patientusername = request.session['patientusername']
        puser = User.objects.get(username=patientusername)
     

        #saving to database.....................

        patient = puser.patient
        diseasename = predicted_disease
        no_of_symp = inputno
        symptomsname = psymptoms
        confidence = confidencescore

        diseaseinfo_new = diseaseinfo(patient=patient,diseasename=diseasename,no_of_symp=no_of_symp,symptomsname=symptomsname,confidence=confidence,consultdoctor=consultdoctor)
        diseaseinfo_new.save()
        

        request.session['diseaseinfo_id'] = diseaseinfo_new.id

        print("disease record saved sucessfully.............................")

        return JsonResponse({'predicteddisease': predicted_disease ,'confidencescore':confidencescore , "consultdoctor": consultdoctor})
   


   
    



   





def pconsultation_history(request):

    if request.method == 'GET':

      patientusername = request.session['patientusername']
      puser = User.objects.get(username=patientusername)
      patient_obj = puser.patient
        
      consultationnew = consultation.objects.filter(patient = patient_obj)
      
    
      return render(request,'patient/consultation_history/consultation_history.html',{"consultation":consultationnew})


def dconsultation_history(request):

    if request.method == 'GET':

      doctorusername = request.session['doctorusername']
      duser = User.objects.get(username=doctorusername)
      doctor_obj = duser.doctor
        
      consultationnew = consultation.objects.filter(doctor = doctor_obj)
      
    
      return render(request,'doctor/consultation_history/consultation_history.html',{"consultation":consultationnew})



def doctor_ui(request):

    if request.method == 'GET':

      doctorid = request.session['doctorusername']
      duser = User.objects.get(username=doctorid)

    
      return render(request,'doctor/doctor_ui/profile.html',{"duser":duser})



      


def dviewprofile(request, doctorusername):

    if request.method == 'GET':

         
         duser = User.objects.get(username=doctorusername)
         r = rating_review.objects.filter(doctor=duser.doctor)
       
         return render(request,'doctor/view_profile/view_profile.html', {"duser":duser, "rate":r} )








       
def  consult_a_doctor(request):


    if request.method == 'GET':

        
        doctortype = request.session['doctortype']
        print(doctortype)
        dobj = doctor.objects.all()
        #dobj = doctor.objects.filter(specialization=doctortype)


        return render(request,'patient/consult_a_doctor/consult_a_doctor.html',{"dobj":dobj})

   


def  make_consultation(request, doctorusername):

    if request.method == 'POST':
       

        patientusername = request.session['patientusername']
        puser = User.objects.get(username=patientusername)
        patient_obj = puser.patient
        
        
        #doctorusername = request.session['doctorusername']
        duser = User.objects.get(username=doctorusername)
        doctor_obj = duser.doctor
        request.session['doctorusername'] = doctorusername


        diseaseinfo_id = request.session['diseaseinfo_id']
        diseaseinfo_obj = diseaseinfo.objects.get(id=diseaseinfo_id)

        consultation_date = date.today()
        status = "active"
        
        consultation_new = consultation( patient=patient_obj, doctor=doctor_obj, diseaseinfo=diseaseinfo_obj, consultation_date=consultation_date,status=status)
        consultation_new.save()

        request.session['consultation_id'] = consultation_new.id

        print("consultation record is saved sucessfully.............................")

         
        return redirect('consultationview',consultation_new.id)



def  consultationview(request,consultation_id):
   
    if request.method == 'GET':

   
      request.session['consultation_id'] = consultation_id
      consultation_obj = consultation.objects.get(id=consultation_id)

      return render(request,'consultation/consultation.html', {"consultation":consultation_obj })

   #  if request.method == 'POST':
   #    return render(request,'consultation/consultation.html' )





def rate_review(request,consultation_id):
   if request.method == "POST":
         
         consultation_obj = consultation.objects.get(id=consultation_id)
         patient = consultation_obj.patient
         doctor1 = consultation_obj.doctor
         rating = request.POST.get('rating')
         review = request.POST.get('review')

         rating_obj = rating_review(patient=patient,doctor=doctor1,rating=rating,review=review)
         rating_obj.save()

         rate = int(rating_obj.rating_is)
         doctor.objects.filter(pk=doctor1).update(rating=rate)
         

         return redirect('consultationview',consultation_id)





def close_consultation(request,consultation_id):
   if request.method == "POST":
         
         consultation.objects.filter(pk=consultation_id).update(status="closed")
         
         return redirect('home')






#-----------------------------chatting system ---------------------------------------------------


def post(request):
    if request.method == "POST":
        msg = request.POST.get('msgbox', None)

        consultation_id = request.session['consultation_id'] 
        consultation_obj = consultation.objects.get(id=consultation_id)

        c = Chat(consultation_id=consultation_obj,sender=request.user, message=msg)

        #msg = c.user.username+": "+msg

        if msg != '':            
            c.save()
            print("msg saved"+ msg )
            return JsonResponse({ 'msg': msg })
    else:
        return HttpResponse('Request must be POST.')



def chat_messages(request):
   if request.method == "GET":

         consultation_id = request.session['consultation_id'] 

         c = Chat.objects.filter(consultation_id=consultation_id)
         return render(request, 'consultation/chat_body.html', {'chat': c})


#-----------------------------chatting system ---------------------------------------------------




from .models import Drug


from .models import Drug,AlternativeDrug

from django.http import JsonResponse
import requests
from urllib.parse import quote

def get_disease_info(request, disease_name):
    """
    Fetch disease information from Wikipedia's API using the disease name provided in the URL.
    """
    # Wikipedia API endpoint
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{disease_name}"

    try:
        # Make a GET request to the Wikipedia API
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            disease_info = {
                "title": data.get("title", "Unknown Disease"),
                "description": data.get("description", "No description available"),
                "extract": data.get("extract", "No additional information available"),
                "link": data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
            return JsonResponse(disease_info, status=200)
        elif response.status_code == 404:
            return JsonResponse({"error": "Disease not found on Wikipedia."}, status=404)
        else:
            return JsonResponse({"error": f"Unexpected response from Wikipedia: {response.status_code}"}, status=500)

    except requests.exceptions.RequestException as e:
        # Catch exceptions related to the request
        return JsonResponse({"error": "An error occurred while fetching disease information.", "details": str(e)}, status=500)