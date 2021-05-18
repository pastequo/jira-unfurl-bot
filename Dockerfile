FROM python:3

COPY requirements.txt ./
COPY consts.py ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
CMD [ "python3", "jira-unfurl-bot.py" ]
