FROM python:3.5.2

ARG PORT_NUMBER=443

EXPOSE $PORT_NUMBER

ENV PORT=$PORT_NUMBER

RUN pip install flask==0.12.2 && \
    pip install pyTelegramBotAPI==2.2.3

COPY Bot /opt/Bot/
CMD ["python", "/opt/Bot/MergeCancelComrade.py"]
