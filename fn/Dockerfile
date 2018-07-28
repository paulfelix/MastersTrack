FROM python:3.6
RUN pip install pymysql

WORKDIR /function
ADD . /function/


ENTRYPOINT ["python", "stats.py"]
