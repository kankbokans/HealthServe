# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import requests
import re
from google.adk.agents import Agent, LlmAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.workflow import Workflow, START, node
from google.adk.events.event import Event
from google.adk.agents.context import Context
from google.genai import types

from app.app_utils.database import DatabaseClient

logger = logging.getLogger(__name__)

# --- Credible Medical Grounding Search Tool ---

def search_medical_knowledge(query: str) -> str:
    """Searches PubMed databases for medical articles and guidelines to answer patient questions.

    Args:
        query: The medical term or symptom query to search for.

    Returns:
        A list of matching medical paper citations and references.
    """
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": 3
        }
        res = requests.get(search_url, params=params, timeout=10)
        if res.status_code != 200:
            return "Could not connect to PubMed database. Please ground using WHO or Mayo Clinic generic guidelines."

        data = res.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return f"No medical papers or guidelines found for query: {query}."

        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        sum_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        sum_res = requests.get(summary_url, params=sum_params, timeout=10)
        if sum_res.status_code != 200:
            return "Fetched articles but failed to retrieve summaries."

        sum_data = sum_res.json()
        articles = []
        for uid in id_list:
            art = sum_data.get("result", {}).get(uid, {})
            title = art.get("title", "No Title")
            source = art.get("source", "PubMed Reference")
            pub_date = art.get("pubdate", "Unknown")
            articles.append(f"- **{title}** ({source}, {pub_date}) - [PMID: {uid}](https://pubmed.ncbi.nlm.nih.gov/{uid}/)")
        return "\n".join(articles)
    except Exception as e:
        return f"Error executing medical literature search: {str(e)}"

# --- Hospital Advisor Database Tools ---

def list_hospitals_tool(city: str = None, zip_code: str = None, hospital_type: str = None, rating: str = None) -> str:
    """Lists and compares hospitals matching the filter criteria from the database.

    Args:
        city: Optional city filter (e.g. 'Boston')
        zip_code: Optional ZIP code filter (e.g. '02111')
        hospital_type: Optional type (e.g. 'Acute Care Hospitals')
        rating: Optional overall rating (e.g. '4', '5')
    """
    try:
        db = DatabaseClient()
        hospitals = db.get_hospitals(city=city, zip_code=zip_code, hospital_type=hospital_type, rating=rating)
        if not hospitals:
            return "No matching hospitals found in the database."

        lines = []
        for h in hospitals:
            lines.append(f"- **{h['Hospital Name']}** ({h['Hospital Type']}) in {h['City']}, {h['State']} (ZIP: {h['ZIP Code']}) - Overall Rating: {h['Hospital overall rating']}/5. Emergency: {h['Emergency Services']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list hospitals: {str(e)}"

def get_hospital_reviews_tool(hospital_name: str = None, state: str = None) -> str:
    """Fetches experience and safety reviews for hospitals from the database.

    Args:
        hospital_name: Optional name of the hospital
        state: Optional 2-letter state code
    """
    try:
        db = DatabaseClient()
        reviews = db.get_reviews(hospital_name=hospital_name, state=state)
        if not reviews:
            return "No patient review or comparison metrics found."

        lines = []
        for r in reviews:
            lines.append(f"- **{r['Hospital Name']}** ({r['City']}, {r['State']}):\n"
                         f"  * Patient Experience: {r['Patient experience national comparison']}\n"
                         f"  * Safety of Care: {r['Safety of care national comparison']}\n"
                         f"  * Readmission: {r['Readmission national comparison']}\n"
                         f"  * Mortality: {r['Mortality national comparison']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to fetch reviews: {str(e)}"

def get_hospital_emergency_info(zip_code: str) -> str:
    """Checks ambulance availability and emergency services for a ZIP code.

    Args:
        zip_code: The 5-digit ZIP code.
    """
    try:
        db = DatabaseClient()
        query = f"SELECT * FROM hospitals_emergency_data WHERE `Zip Code` = '{db.sanitize_str(zip_code)}';"
        rows = db._execute_sql(query)
        if not rows:
            return f"No emergency or ambulance availability data found for ZIP code {zip_code}."

        lines = []
        for row in rows:
            lines.append(f"- **{row['Hospital Name']}** (ZIP {row['Zip Code']}): Ambulance Available: {row['Ambulance Available']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to get emergency details: {str(e)}"

# --- Booking Coordinator Database Tools ---

def list_doctors(specialization: str = None) -> str:
    """Lists doctors and their specializations from the database.

    Args:
        specialization: Optional specialization to search (e.g. 'Cardiology', 'Orthopedics')
    """
    try:
        db = DatabaseClient()
        doctors = db.get_doctors(specialization=specialization)
        if not doctors:
            return "No doctors found matching that specialization."
        lines = []
        for d in doctors:
            lines.append(f"- **Dr. {d['name']}** - Specialization: {d['specialization']} (Doctor ID: {d['id']}, Contact: {d['contact']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list doctors: {str(e)}"

def list_doctor_slots(doctor_id: int) -> str:
    """Lists active available slot times for a doctor from the database.

    Args:
        doctor_id: The integer ID of the doctor
    """
    try:
        db = DatabaseClient()
        slots = db.get_slots(doctor_id=doctor_id)
        if not slots:
            return "No available slot times found for this doctor."
        lines = []
        for s in slots:
            lines.append(f"- Slot ID: {s['id']} at `{s['slot_datetime']}`")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to list slots: {str(e)}"

def book_appointment_by_name(doctor_id: int, slot_datetime: str, patient_name: str) -> str:
    """Books an appointment slot for a doctor.

    Args:
        doctor_id: The integer ID of the doctor
        slot_datetime: Datetime slot formatted as YYYY-MM-DD HH:MM:SS
        patient_name: Name of the patient
    """
    try:
        db = DatabaseClient()
        res = db.book_appointment(doctor_id=doctor_id, slot_datetime=slot_datetime, patient_name=patient_name)
        return res.get("message", "Responded without message.")
    except Exception as e:
        return f"Booking failed: {str(e)}"

def cancel_appointment_by_id(appointment_id: int) -> str:
    """Cancels an existing appointment by booking ID.

    Args:
        appointment_id: The integer ID of the appointment
    """
    try:
        db = DatabaseClient()
        res = db.cancel_appointment(appointment_id=appointment_id)
        return res.get("message", "Responded without message.")
    except Exception as e:
        return f"Cancellation failed: {str(e)}"

def reschedule_appointment_by_id(appointment_id: int, new_slot_datetime: str) -> str:
    """Reschedules an appointment to a new slot datetime.

    Args:
        appointment_id: The integer ID of the appointment
        new_slot_datetime: Datetime slot formatted as YYYY-MM-DD HH:MM:SS
    """
    try:
        db = DatabaseClient()
        res = db.update_appointment(appointment_id=appointment_id, new_slot_datetime=new_slot_datetime)
        return res.get("message", "Responded without message.")
    except Exception as e:
        return f"Rescheduling failed: {str(e)}"

# --- Intent Classifier & Agents ---

classifier_agent = LlmAgent(
    name="classifier",
    model=Gemini(model="gemini-flash-latest"),
    instruction="Classify the user input prompt. Answer with ONLY one of the exact strings: 'medical_query', 'hospital_query', 'booking_query', 'general_query'. Do not output any other text or reasoning.",
)

medical_expert_agent = LlmAgent(
    name="medical_expert",
    model=Gemini(model="gemini-flash-latest"),
    instruction="You are a grounded Medical Expert assistant. Answer the user's symptoms, sickness, or disease questions using the search_medical_knowledge tool. Cite the articles you find, and prioritize grounding your answer in guidelines from NIH, PubMed, WebMD, WHO, and Mayo Clinic.",
    tools=[search_medical_knowledge],
)

hospital_advisor_agent = LlmAgent(
    name="hospital_advisor",
    model=Gemini(model="gemini-flash-latest"),
    instruction="You are a Hospital Advisor. Use your tools to find, list, and compare hospital facilities, ratings, ratings footnotes, diagnostics tests, and ambulance services. Help the user compare hospitals on ratings, types, and experience reviews.",
    tools=[list_hospitals_tool, get_hospital_reviews_tool, get_hospital_emergency_info],
)

appointment_coordinator_agent = LlmAgent(
    name="appointment_coordinator",
    model=Gemini(model="gemini-flash-latest"),
    instruction="You are an Appointment Coordinator. You help patients find doctors, list slot times, book appointments, cancel bookings, or reschedule bookings. Cite ID numbers and slot times. Ground your answers strictly in the tool outputs. If the user wants to book, reschedule, or cancel but has not provided details (like doctor ID, slot datetime, or patient name), ask for them.",
    tools=[list_doctors, list_doctor_slots, book_appointment_by_name, cancel_appointment_by_id, reschedule_appointment_by_id],
)

general_agent = LlmAgent(
    name="general_agent",
    model=Gemini(model="gemini-flash-latest"),
    instruction="You are Healy, a friendly HealthServeAI assistant. Ground your answer in guiding the user on how they can navigate the system. Introduce yourself as Healy and mention they can compare hospitals, read patient reviews, chat about symptoms, and book doctor appointments using the tabs on the left.",
)

# --- Router Node ---

@node(rerun_on_resume=True)
async def router_node(ctx: Context, node_input: types.Content) -> Event:
    """Classifies user intent and routes the query to the correct specialist node."""
    user_msg = ""
    if node_input and node_input.parts:
        user_msg = "".join(part.text for part in node_input.parts if part.text)

    # Call Gemini API directly (avoiding ADK node event streaming leak)
    from google.genai import Client
    client = Client()
    intent = "general_query"
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction="Classify the user input prompt. Answer with ONLY one of the exact strings: 'medical_query', 'hospital_query', 'booking_query', 'general_query'. Do not output any other text or reasoning."
            )
        )
        intent_text = response.text.strip().lower() if response.text else "general_query"
        if "medical" in intent_text:
            intent = "medical_query"
        elif "hospital" in intent_text:
            intent = "hospital_query"
        elif "booking" in intent_text or "appointment" in intent_text:
            intent = "booking_query"
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")

    logger.info(f"Classified intent: {intent} for message: {user_msg}")
    return Event(output=node_input, route=intent)

# --- ADK 2.0 Graph Workflow ---

root_agent = Workflow(
    name="root_agent",
    edges=[
        (START, router_node),
        (router_node, {
            "medical_query": medical_expert_agent,
            "hospital_query": hospital_advisor_agent,
            "booking_query": appointment_coordinator_agent,
            "general_query": general_agent,
        })
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
