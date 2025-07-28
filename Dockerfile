FROM fnproject/python:3.9

WORKDIR /function
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY func.py .

ENV PYTHONPATH=/function
ENTRYPOINT ["python", "-m", "fdk", "func.py", "handle"]