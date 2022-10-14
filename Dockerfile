# docker build -t telespy:latest .
# docker run -it -v $PWD:/app telespy

FROM python:3.10

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#COPY . .

CMD [ "python", "-m", "telespy" ]
