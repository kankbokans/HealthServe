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
import requests
import google.auth
import google.auth.transport.requests
from pymysql.converters import escape_string

logger = logging.getLogger(__name__)

class DatabaseClient:
    """Helper client to connect to Google Cloud SQL via Admin API executeSql."""

    def __init__(self):
        # Retrieve credentials and project ID
        self.credentials, self.project_id = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.instance_id = "healthserveai"
        self.database_name = "healthserveai"

    def _refresh_token(self):
        """Refreshes the OAuth credentials to get a fresh bearer token."""
        auth_req = google.auth.transport.requests.Request()
        self.credentials.refresh(auth_req)

    def _execute_sql(self, sql: str) -> list[dict]:
        """Executes a SQL query against the database and returns parsed rows."""
        self._refresh_token()

        url = f"https://sqladmin.googleapis.com/v1/projects/{self.project_id}/instances/{self.instance_id}/executeSql"
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "sqlStatement": sql,
            "database": self.database_name,
            "autoIamAuthn": True
        }

        logger.debug(f"Executing SQL: {sql}")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error(f"SQL execution error: {response.text}")
            raise Exception(f"Database query failed: {response.text}")

        return self._parse_response(response.json())

    def _parse_response(self, response_json: dict) -> list[dict]:
        """Converts Cloud SQL executeSql JSON response format to list[dict]."""
        results = []
        if not response_json or "results" not in response_json:
            return results

        for r in response_json["results"]:
            columns = [c["name"] for c in r.get("columns", [])]
            for row in r.get("rows", []):
                row_values = []
                for val in row.get("values", []):
                    if "nullValue" in val:
                        row_values.append(None)
                    else:
                        row_values.append(val.get("value"))
                results.append(dict(zip(columns, row_values)))
        return results

    def sanitize_str(self, val: str) -> str:
        """Sanitizes string inputs to prevent SQL Injection."""
        if val is None:
            return ""
        # Remove double dashes to prevent comment-based injections
        no_comments = val.replace("--", "")
        # Keep alphanumeric, spaces, dots, hyphens, and common punctuation
        clean = re.sub(r"[^\w\s\.\,\-\@\:\/\#]", "", no_comments)
        return escape_string(clean).strip()

    def get_hospitals(self, city: str = None, zip_code: str = None, hospital_type: str = None, rating: str = None) -> list[dict]:
        """Fetches and compares hospitals based on filters."""
        query = "SELECT `Hospital Name`, `Hospital Type`, `Hospital Ownership`, `Hospital overall rating`, `Address`, `City`, `State`, `ZIP Code`, `Phone Number`, `Emergency Services`, `Mortality national comparison`, `Safety of care national comparison` FROM Hospital_Information_with_Lab_Tests WHERE 1=1"

        if city:
            query += f" AND `City` = '{self.sanitize_str(city)}'"
        if zip_code:
            # ZIP codes are alphanumeric or numeric 5 digits
            clean_zip = re.sub(r"[^\w\s\-]", "", zip_code)
            query += f" AND `ZIP Code` = '{clean_zip}'"
        if hospital_type:
            query += f" AND `Hospital Type` = '{self.sanitize_str(hospital_type)}'"
        if rating:
            query += f" AND `Hospital overall rating` = '{self.sanitize_str(rating)}'"

        # Group by hospital name to remove duplicates (since lab test packages produce multiple rows)
        query += " GROUP BY `Hospital Name`, `Hospital Type`, `Hospital Ownership`, `Hospital overall rating`, `Address`, `City`, `State`, `ZIP Code`, `Phone Number`, `Emergency Services`, `Mortality national comparison`, `Safety of care national comparison` LIMIT 50;"
        return self._execute_sql(query)

    def get_reviews(self, hospital_name: str = None, state: str = None) -> list[dict]:
        """Fetches patient experience and national comparisons for hospitals."""
        query = "SELECT `Hospital Name`, `City`, `State`, `Patient experience national comparison`, `Safety of care national comparison`, `Readmission national comparison`, `Mortality national comparison` FROM Hospital_Information_with_Lab_Tests WHERE 1=1"

        if hospital_name:
            query += f" AND `Hospital Name` LIKE '%{self.sanitize_str(hospital_name)}%'"
        if state:
            # States are 2-letter codes or strings
            clean_state = re.sub(r"[^a-zA-Z\s]", "", state)[:50]
            query += f" AND `State` = '{clean_state}'"

        query += " GROUP BY `Hospital Name`, `City`, `State`, `Patient experience national comparison`, `Safety of care national comparison`, `Readmission national comparison`, `Mortality national comparison` LIMIT 50;"
        return self._execute_sql(query)

    def get_diagnostics(self, test_name: str = None) -> list[dict]:
        """Fetches diagnostic tests and their providers."""
        query = "SELECT `Hospital Name`, `Diagnostic Test`, `Health Package`, `Preparation Instructions` FROM Hospital_Information_with_Lab_Tests WHERE `Diagnostic Test` IS NOT NULL AND `Diagnostic Test` != ''"
        if test_name:
            query += f" AND `Diagnostic Test` LIKE '%{self.sanitize_str(test_name)}%'"
        query += " LIMIT 50;"
        return self._execute_sql(query)

    def get_appointments(self) -> list[dict]:
        """Fetches all active booked appointments joined with doctor details."""
        query = """
            SELECT a.id, a.doctor_id, a.slot_datetime, a.patient_name, a.status, d.name as doctor_name, d.specialization
            FROM appointments a
            JOIN doctors_info_data d ON a.doctor_id = d.id
            WHERE a.status = 'booked'
            ORDER BY a.slot_datetime ASC;
        """
        return self._execute_sql(query)

    def get_doctors(self, specialization: str = None) -> list[dict]:
        """Lists doctors and their specializations."""
        query = "SELECT id, name, specialization, contact FROM doctors_info_data WHERE 1=1"
        if specialization:
            query += f" AND specialization LIKE '%{self.sanitize_str(specialization)}%'"
        return self._execute_sql(query)

    def get_slots(self, doctor_id: int) -> list[dict]:
        """Lists active available slots for a specific doctor."""
        # Convert doctor_id to int to assert safety
        doc_id = int(doctor_id)
        query = f"SELECT id, slot_datetime FROM doctors_slot_data WHERE doctor_id = {doc_id} AND is_available = 1 ORDER BY slot_datetime ASC;"
        return self._execute_sql(query)

    def book_appointment(self, doctor_id: int, slot_datetime: str, patient_name: str) -> dict:
        """Books an appointment by writing to the database."""
        doc_id = int(doctor_id)
        clean_patient = self.sanitize_str(patient_name)
        # Ensure slot_datetime is in a correct datetime format
        if not re.match(r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$", slot_datetime.strip()):
            raise ValueError("Invalid datetime format. Expected 'YYYY-MM-DD HH:MM:SS'")

        # Check if the slot is available
        check_query = f"SELECT id FROM doctors_slot_data WHERE doctor_id = {doc_id} AND slot_datetime = '{slot_datetime}' AND is_available = 1;"
        available_slots = self._execute_sql(check_query)
        if not available_slots:
            return {"success": False, "message": "Selected slot is not available or already booked."}

        # Perform the booking inside a transaction (sequential execution)
        insert_query = f"INSERT INTO appointments (doctor_id, slot_datetime, patient_name, status) VALUES ({doc_id}, '{slot_datetime}', '{clean_patient}', 'booked');"
        self._execute_sql(insert_query)

        update_query = f"UPDATE doctors_slot_data SET is_available = 0 WHERE doctor_id = {doc_id} AND slot_datetime = '{slot_datetime}';"
        self._execute_sql(update_query)

        # Find the generated appointment ID
        id_query = f"SELECT id FROM appointments WHERE doctor_id = {doc_id} AND slot_datetime = '{slot_datetime}' AND patient_name = '{clean_patient}' ORDER BY created_at DESC LIMIT 1;"
        appt = self._execute_sql(id_query)
        appt_id = appt[0]['id'] if appt else None

        return {
            "success": True,
            "appointment_id": appt_id,
            "message": f"Appointment booked successfully for {clean_patient}!"
        }

    def cancel_appointment(self, appointment_id: int) -> dict:
        """Cancels an appointment and marks the doctor's slot as available."""
        appt_id = int(appointment_id)

        # Find doctor_id and slot_datetime first
        find_query = f"SELECT doctor_id, slot_datetime FROM appointments WHERE id = {appt_id} AND status = 'booked';"
        appt = self._execute_sql(find_query)
        if not appt:
            return {"success": False, "message": "No active booking found for the provided appointment ID."}

        doc_id = appt[0]["doctor_id"]
        slot_dt = appt[0]["slot_datetime"]

        # Cancel appointment and release slot
        cancel_query = f"UPDATE appointments SET status = 'cancelled' WHERE id = {appt_id};"
        self._execute_sql(cancel_query)

        release_query = f"UPDATE doctors_slot_data SET is_available = 1 WHERE doctor_id = {doc_id} AND slot_datetime = '{slot_dt}';"
        self._execute_sql(release_query)

        return {"success": True, "message": "Appointment cancelled successfully."}

    def update_appointment(self, appointment_id: int, new_slot_datetime: str) -> dict:
        """Reschedules an appointment to a new slot."""
        appt_id = int(appointment_id)

        if not re.match(r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$", new_slot_datetime.strip()):
            raise ValueError("Invalid datetime format. Expected 'YYYY-MM-DD HH:MM:SS'")

        # Find the existing appointment details
        find_query = f"SELECT doctor_id, slot_datetime, patient_name FROM appointments WHERE id = {appt_id} AND status = 'booked';"
        appt = self._execute_sql(find_query)
        if not appt:
            return {"success": False, "message": "No active booking found for the provided appointment ID."}

        doc_id = appt[0]["doctor_id"]
        old_slot_dt = appt[0]["slot_datetime"]
        patient_name = appt[0]["patient_name"]

        # Verify new slot is available
        check_query = f"SELECT id FROM doctors_slot_data WHERE doctor_id = {doc_id} AND slot_datetime = '{new_slot_datetime}' AND is_available = 1;"
        new_available = self._execute_sql(check_query)
        if not new_available:
            return {"success": False, "message": "The selected new slot is not available."}

        # Update appointment, release old slot, occupy new slot
        update_appt = f"UPDATE appointments SET slot_datetime = '{new_slot_datetime}' WHERE id = {appt_id};"
        self._execute_sql(update_appt)

        release_old = f"UPDATE doctors_slot_data SET is_available = 1 WHERE doctor_id = {doc_id} AND slot_datetime = '{old_slot_dt}';"
        self._execute_sql(release_old)

        occupy_new = f"UPDATE doctors_slot_data SET is_available = 0 WHERE doctor_id = {doc_id} AND slot_datetime = '{new_slot_datetime}';"
        self._execute_sql(occupy_new)

        return {"success": True, "message": f"Appointment rescheduled to {new_slot_datetime}."}
