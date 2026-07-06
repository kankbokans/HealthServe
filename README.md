# HealthServeAI - Patient Dashboard & AI Healthcare Assistant

HealthServeAI is an interactive patient dashboard and intelligent booking platform. It features an interactive single-page web dashboard for searching/comparing hospitals and booking doctor appointments, coupled with **Healy**, an AI health assistant driven by a multi-agent workflow.

---

## 🚀 Key Features

### 1. Hospital Search & Comparison
- Filter hospitals dynamically by **State** (dropdown selector of all US states) and **Type** (Acute Care, Critical Access, Childrens).
- Display ratings, emergency service status, and patient satisfaction metrics in a clean, scrollable results table.

### 2. Live Appointment Booking & Rescheduling (2026 Slots)
- Seeding of **88,480 fresh, real-time availability slots** for late 2026 (July to December) across all 28 doctors.
- Booking confirmation, cancellation, and rescheduling forms.
- The reschedule modal allows users to view, enter, and edit the patient name in the database (resolving hardcoded defaults).

### 3. Chat with Healy (AI Assistant)
- **Intent Routing**: User queries are analyzed and automatically routed to specialized sub-agents (`medical_expert`, `hospital_advisor`, `appointment_coordinator`, or `general_agent`).
- **Conversational Memory**: A stateful callback (`before_model_callback`) reads session history events, de-duplicates consecutive messages, and injects context turns directly into the Gemini LLM request for multi-turn conversations.
- **Medical Grounding**: Symptom-based routing prompts the `medical_expert` sub-agent to query the federal **NCBI Entrez PubMed API** programmatically for verified medical papers and citations.

---

## 📁 Repository Structure

```text
HealthSenseAI/
├── Healthserve data/      # Source CSV files (doctor slot availability, reviews, info)
├── Specs/                 # Design requirements and query specifications
├── healthserveai/         # Core application directory
│   ├── app/               # FastAPI application backend
│   │   ├── agent.py       # ADK 2.0 graph workflow, nodes, and tools
│   │   ├── server.py      # HTTP server endpoints, validators, and route schemas
│   │   └── app_utils/     # App utilities and helpers
│   ├── frontend/          # Single-page web dashboard frontend (HTML/CSS/JS)
│   ├── tests/             # Pytest unit and integration test suite
│   ├── system_design.drawio # System architecture diagram
│   └── pyproject.toml     # Python dependencies configuration
└── README.md              # Root-level project documentation
```

---

## 🛠️ Database Schema

The system integrates with a Cloud SQL MySQL database (`healthserve` / `healthserveai`) with the following schemas:

*   **`hospital_info_data`**: Details of hospital locations, city, state, types, and baseline data.
*   **`doctors_info_data`**: Doctor directories, identifiers, names, and specializations (e.g. Pediatrics, Cardiology).
*   **`doctors_slot_data`**: Real-time slot availability flags (`is_available`: 0 or 1) and timestamps.
*   **`appointments`**: Booked patient records linking appointment IDs, doctor IDs, slot datetimes, patient names, and statuses (`booked`, `cancelled`).

---

## 🚦 Endpoint Specifications

| Endpoint | Method | Request Payload | Description |
|---|---|---|---|
| `/api/hospitals` | `GET` | *Query params: `state`, `type`* | Lists and compares hospitals. |
| `/api/reviews` | `GET` | — | Retrieves all patient reviews. |
| `/api/doctors` | `GET` | — | Lists all available doctors. |
| `/api/doctors/{id}/slots` | `GET` | — | Retrieves available slot datetimes for a doctor. |
| `/api/appointments` | `GET` | — | Retrieves all active booked appointments. |
| `/api/appointments` | `POST` | `doctor_id`, `slot_datetime`, `patient_name` | Creates a new booking. |
| `/api/appointments/cancel`| `POST` | `appointment_id` | Cancels a booking. |
| `/api/appointments/update`| `POST` | `appointment_id`, `new_slot_datetime`, `patient_name` (optional) | Reschedules a booking. |
| `/api/chat` | `POST` | `message`, `session_id` | Passes messages to Healy's workflow. |

---

## 💻 Local Setup & Development

### 1. Prerequisites
- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (Astral Python Package Manager)
- A Google Cloud Platform project with Vertex AI enabled and Application Default Credentials (ADC) configured.

### 2. Install Dependencies
Run the installation from the `healthserveai` subdirectory:
```bash
cd healthserveai
uv sync
```

### 3. Environment Configuration
Create a `.env` file in the root directory (or copy the pre-configured environment settings) pointing to your database instance:
```ini
DB_USER=your_db_user
DB_PASS=your_db_password
DB_NAME=healthserve
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 4. Running the Development Server
Launch the FastAPI development environment with auto-reload:
```bash
.venv\Scripts\python.exe -m uvicorn app.server:app --reload --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser to access the dashboard.

### 5. Running Tests
Run the complete unit and query integration test suite using `pytest`:
```bash
.venv\Scripts\pytest.exe tests/unit
```
