FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python src/ingest/fred.py
RUN python src/ingest/fdic.py
RUN python src/transform/transform_fred.py
RUN python src/transform/transform_fdic.py
RUN python src/transform/merge.py
RUN python src/transform/load.py

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
