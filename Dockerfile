FROM python:3.8

RUN mkdir /app
WORKDIR /app

RUN pip install fastapi uvicorn
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

ADD ./html /app/html

COPY ./__init__.py /app
COPY ./config.py /app
COPY ./database.py /app
COPY ./main.py /app


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]