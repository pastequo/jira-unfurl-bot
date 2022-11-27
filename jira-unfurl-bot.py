import os
import jira

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

JIRA_SERVER = "https://issues.redhat.com"

jira_access_token = os.environ.get("JIRA_ACCESS_TOKEN")
if jira_access_token is None:
    raise ValueError("You must provide JIRA_ACCESS_TOKEN env-var")

jira_client = jira.JIRA(JIRA_SERVER, token_auth=jira_access_token)

# Check liveness
@app.event("app_mention")
def event_test(say):
    say("I'm alive")


@app.event("link_shared")
def got_link(client, payload):
    for link in payload["links"]:
        url = link["url"]
        issue_id = url.split("/")[-1]
        issue = jira_client.issue(issue_id)

        _payload = get_payload(url, issue)
        channel_id = payload["channel"]
        client.chat_unfurl(
            channel=channel_id,
            ts=payload["message_ts"],
            unfurls=_payload,
        )


def get_payload(url, issue):
    key = issue.key
    status = issue.fields.status.name
    summary = issue.fields.summary
    unfurl_text = f":jira: *{key}* [*{status}*] : {summary}"

    payload = {
        url: {
            "color": "#025BA6",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": unfurl_text,
                    }
                },
            ]
        }
    }
    return payload

if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
