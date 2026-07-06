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

import os
import re
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.app_utils.database import DatabaseClient
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.agent import app as adk_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HealthSenseAI API Server")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate database client and ADK agent runner
db_client = DatabaseClient()
agent_runner = InMemoryRunner(app=adk_app)

# Session store to map web sessions to runner sessions
sessions_map = {}

# --- Pydantic Request Models & Input Validation ---

class BookingRequest(BaseModel):
    doctor_id: int = Field(..., description="ID of the doctor")
    slot_datetime: str = Field(..., description="Datetime slot string formatted as YYYY-MM-DD HH:MM:SS")
    patient_name: str = Field(..., description="Name of the patient")

    @field_validator("patient_name")
    @classmethod
    def validate_patient_name(cls, v: str) -> str:
        # Strict validation: alphabetic, spaces, dots, hyphens, length 2-100
        if not re.match(r"^[a-zA-Z\s\.\-]{2,100}$", v):
            raise ValueError("Patient name must be between 2 and 100 characters and contain only letters, spaces, dots, or hyphens.")
        return v.strip()

    @field_validator("slot_datetime")
    @classmethod
    def validate_slot_datetime(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$", v):
            raise ValueError("Slot datetime must be in format: 'YYYY-MM-DD HH:MM:SS'")
        return v.strip()

class CancelRequest(BaseModel):
    appointment_id: int = Field(..., description="ID of the appointment to cancel")

class UpdateRequest(BaseModel):
    appointment_id: int = Field(..., description="ID of the appointment to update")
    new_slot_datetime: str = Field(..., description="New slot datetime string formatted as YYYY-MM-DD HH:MM:SS")
    patient_name: Optional[str] = Field(None, description="Updated name of the patient")

    @field_validator("new_slot_datetime")
    @classmethod
    def validate_new_slot_datetime(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$", v):
            raise ValueError("New slot datetime must be in format: 'YYYY-MM-DD HH:MM:SS'")
        return v.strip()

    @field_validator("patient_name")
    @classmethod
    def validate_patient_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z\s\.\-]{2,100}$", v):
            raise ValueError("Patient name must be between 2 and 100 characters and contain only letters, spaces, dots, or hyphens.")
        return v.strip()

class ChatRequest(BaseModel):
    message: str = Field(..., description="The chat message from the user")
    session_id: str = Field(..., description="The chat session ID")

# --- API Endpoints ---

@app.get("/api/hospitals")
def get_hospitals(
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    hospital_type: Optional[str] = Query(None),
    rating: Optional[str] = Query(None)
):
    """Filters and lists hospitals."""
    try:
        # Perform additional parameter regex checks at route level
        if zip_code and not re.match(r"^\w{1,10}$", zip_code):
            raise HTTPException(status_code=400, detail="Invalid ZIP Code format.")
        if state and not re.match(r"^[a-zA-Z]{1,10}$", state):
            raise HTTPException(status_code=400, detail="Invalid state format.")

        hospitals = db_client.get_hospitals(
            city=city,
            state=state,
            zip_code=zip_code,
            hospital_type=hospital_type,
            rating=rating
        )
        return {"success": True, "data": hospitals}
    except Exception as e:
        logger.error(f"Error getting hospitals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reviews")
def get_reviews(
    hospital_name: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    """Filters and lists hospital reviews and experience metrics."""
    try:
        if state and not re.match(r"^[a-zA-Z\s]{1,50}$", state):
            raise HTTPException(status_code=400, detail="Invalid state format.")

        reviews = db_client.get_reviews(hospital_name=hospital_name, state=state)
        return {"success": True, "data": reviews}
    except Exception as e:
        logger.error(f"Error getting reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/appointments")
def get_active_appointments():
    """Lists all active appointments."""
    try:
        appointments = db_client.get_appointments()
        return {"success": True, "data": appointments}
    except Exception as e:
        logger.error(f"Error getting active appointments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/doctors")
def get_doctors(specialization: Optional[str] = Query(None)):
    """Lists all doctors with optional specialization filter."""
    try:
        doctors = db_client.get_doctors(specialization=specialization)
        return {"success": True, "data": doctors}
    except Exception as e:
        logger.error(f"Error getting doctors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/doctors/{doctor_id}/slots")
def get_doctor_slots(doctor_id: int):
    """Lists available slots for a specific doctor."""
    try:
        slots = db_client.get_slots(doctor_id=doctor_id)
        return {"success": True, "data": slots}
    except Exception as e:
        logger.error(f"Error getting doctor slots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/appointments")
def book_appointment(req: BookingRequest):
    """Creates a new appointment booking."""
    try:
        result = db_client.book_appointment(
            doctor_id=req.doctor_id,
            slot_datetime=req.slot_datetime,
            patient_name=req.patient_name
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/appointments/cancel")
def cancel_appointment(req: CancelRequest):
    """Cancels an existing appointment."""
    try:
        result = db_client.cancel_appointment(appointment_id=req.appointment_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/appointments/update")
def update_appointment(req: UpdateRequest):
    """Reschedules an appointment to a new slot."""
    try:
        result = db_client.update_appointment(
            appointment_id=req.appointment_id,
            new_slot_datetime=req.new_slot_datetime,
            patient_name=req.patient_name
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error updating appointment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_agent(req: ChatRequest):
    """Sends a chat message to the ADK 2.0 agent graph."""
    try:
        user_id = "healthserve_web_user"
        session_id = req.session_id

        # Map or create session in the runner
        if session_id not in sessions_map:
            session = await agent_runner.session_service.create_session(
                app_name="app", user_id=user_id
            )
            sessions_map[session_id] = session.id

        runner_session_id = sessions_map[session_id]

        response_text = ""
        # Invoke agent workflow
        async for event in agent_runner.run_async(
            user_id=user_id,
            session_id=runner_session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part.from_text(text=req.message)]
            ),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        # If agent finished but didn't yield text directly, check output or fallback
        if not response_text.strip():
            response_text = "I've processed your query successfully but generated no text response."

        return {"success": True, "response": response_text}
    except Exception as e:
        logger.error(f"Error running agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend static files last so API routes are evaluated first
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    logger.warning(f"Frontend static directory not found at: {frontend_dir}")
