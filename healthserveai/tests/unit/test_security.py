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

import pytest
from pydantic import ValidationError
from app.server import BookingRequest, UpdateRequest
from app.app_utils.database import DatabaseClient

def test_pydantic_patient_name_validation():
    """Asserts that patient names conform to safe regex rules and length limits."""
    # Valid name should succeed
    req = BookingRequest(doctor_id=1, slot_datetime="2026-07-05 10:00:00", patient_name="John Doe")
    assert req.patient_name == "John Doe"

    # Names with SQL injection structures must be blocked by Pydantic validation
    with pytest.raises(ValidationError):
        BookingRequest(doctor_id=1, slot_datetime="2026-07-05 10:00:00", patient_name="John'; DROP TABLE appointments;--")

    # Names containing numeric characters or invalid special characters must be blocked
    with pytest.raises(ValidationError):
        BookingRequest(doctor_id=1, slot_datetime="2026-07-05 10:00:00", patient_name="John123_Doe")

def test_pydantic_datetime_validation():
    """Asserts that doctor slot times are formatted precisely as expected."""
    # Valid datetime format
    req = BookingRequest(doctor_id=1, slot_datetime="2026-07-05 10:00:00", patient_name="John Doe")
    assert req.slot_datetime == "2026-07-05 10:00:00"

    # Malformed datetime format must be rejected
    with pytest.raises(ValidationError):
        BookingRequest(doctor_id=1, slot_datetime="2026/07/05 10:00:00", patient_name="John Doe")

    with pytest.raises(ValidationError):
        BookingRequest(doctor_id=1, slot_datetime="2026-07-05 10:00", patient_name="John Doe")

def test_database_client_sanitization():
    """Asserts that inputs passed to database queries are escaped and cleaned of dangerous characters."""
    db = DatabaseClient()

    # Check that SQL control characters are stripped or escaped
    dirty_city = "Boston'; DROP TABLE Hospital_Information_with_Lab_Tests; --"
    clean_city = db.sanitize_str(dirty_city)

    # Ensure raw single quotes are not present (either stripped or escaped as \')
    assert "'" not in clean_city or "\\'" in clean_city
    # Ensure double dashes (comment symbols) are stripped or harmless
    assert "--" not in clean_city
