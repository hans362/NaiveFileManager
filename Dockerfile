FROM python:3.12-slim

RUN mkdir /app

COPY . /app

RUN pip install -r /app/requirements.txt

WORKDIR /app

CMD ["fastapi", "run", "main.py", "--port", "8000"]