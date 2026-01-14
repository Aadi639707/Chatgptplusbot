FROM python:3.9

# Working directory set karein
WORKDIR /code

# Sabhi files copy karein
COPY . .

# Libraries install karein
RUN pip install --no-cache-dir -r requirements.txt

# Bot start karne ki command
CMD ["python", "main.py"]
