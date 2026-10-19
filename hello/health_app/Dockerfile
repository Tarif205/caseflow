# Start from the official image that already has Python 3.12 installed.
# "slim" leaves out compilers and tools we do not need, so the image is small.
FROM python:3.12-slim

# Make a folder /app inside the image and work from there from now on.
WORKDIR /app

# Copy ONLY the library list first, then install it.
# Docker remembers (caches) each step. Because main.py is not copied yet,
# editing main.py later does not force this slow install step to run again.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the code (main.py) into /app.
COPY . .

# Note for readers that the app uses port 8000. This line opens nothing.
EXPOSE 8000

# Runs every time a container starts. Same command as on the laptop, plus
# --host 0.0.0.0 so visitors from outside the container can reach it.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
