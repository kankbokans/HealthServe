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
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.agent import app as adk_app

@pytest.mark.asyncio
async def test_specs_example_queries():
    """Validates the agent graph against real queries and expected response contexts from specs.md."""
    runner = InMemoryRunner(app=adk_app)
    session = await runner.session_service.create_session(
        app_name="app", user_id="test_user"
    )

    test_cases = [
        {
            "query": "Find available doctors for a dermatology consultation this week.",
            "keywords": ["doctor", "specialization", "dermatology", "available", "slot"]
        },
        {
            "query": "What hospitals specialize in cardiology near me?",
            "keywords": ["cardiology", "hospital", "department", "rating", "city", "state", "zip", "location", "provide"]
        },
        {
            "query": "Any ambulance available at 94404?",
            "keywords": ["ambulance", "available", "emergency", "94404"]
        },
        {
            "query": "What tests should I take for persistent headaches?",
            "keywords": ["headache", "test", "medical"]
        },
        {
            "query": "What would be the preparation instructions for cancer screening?",
            "keywords": ["preparation", "instruction", "cancer", "screening", "hospital"]
        }
    ]

    for tc in test_cases:
        response_text = ""
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=tc["query"])]),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        # Verify the response is not empty and contains expected context terms
        assert response_text.strip(), f"Empty response for query: {tc['query']}"

        matched_kws = [kw for kw in tc["keywords"] if kw in response_text.lower()]
        assert len(matched_kws) > 0, f"Query '{tc['query']}' response did not contain expected keywords {tc['keywords']}. Got: {response_text}"
