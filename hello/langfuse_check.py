# Path helps us locate .env regardless of the terminal's folder.
from pathlib import Path

# These libraries load settings and connect to Langfuse.
from dotenv import load_dotenv
from langfuse import get_client

# Go from this file to hello/, then to the project root.
project_root = Path(__file__).resolve().parent.parent

# Load the project settings without printing any secrets.
load_dotenv(project_root / ".env")

# Create the client using the Langfuse environment variables.
langfuse = get_client()

# Start recording one operation named day-0-check.
with langfuse.start_as_current_observation(
    as_type="span",
    name="day-0-check",
    input="Testing the tracing connection",
) as span:
    # Record a simple result; no AI model is involved.
    span.update(output="The test operation finished")

# Wait for queued records to be exported before Python exits.
langfuse.flush()

# Dashboard confirmation is still needed to prove delivery.
print("Export attempted. Look for day-0-check in Langfuse.")