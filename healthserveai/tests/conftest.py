import os

# Ensure GEMINI_API_KEY and GOOGLE_API_KEY are deleted from environment
# before any google-genai clients are imported or initialized.
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]
if "GOOGLE_API_KEY" in os.environ:
    del os.environ["GOOGLE_API_KEY"]

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_PROJECT"] = "gen-lang-client-0825174628"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-east1"
