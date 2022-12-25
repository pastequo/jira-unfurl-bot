import os
import jira

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

JIRA_SERVER = "https://issues.redhat.com"
ISSUE_TYPE_TO_COLOR = {
    "Epic": "#4c00b0",
    "Task" : "#1c4966",
    "Bug": "#7c0a02",
    "Story": "#3bb143",
}

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
        if "browse" in url:
            issue_id = url.split("/")[-1]
            issue = jira_client.issue(issue_id)

            _payload = get_issue_payload(issue, url)
        elif "versions" in url:
            version_id = url.split("/")[-1]
            version = jira_client.version(version_id)

            _payload = get_version_payload(version, url)

        channel_id = payload["channel"]
        client.chat_unfurl(
            channel=channel_id,
            ts=payload["message_ts"],
            unfurls=_payload,
        )


def get_version_payload(version, url):
    release_info = f"Released at {version.releaseDate}" if version.released else "Unreleased"
    description = version.raw.get("description", "[No description given]")
    return {
        url: {
            "color": "#ff8b3d",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":jira: *{version.name}* [*{release_info}*] : {description}",
                    }
                },
            ]
        }
    }


def get_issue_payload(issue, url):
    color = ISSUE_TYPE_TO_COLOR.get(issue.fields.issuetype.name, "#025BA6")
    return {
        url: {
            "color": color,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":jira: *{issue.key}* [*{issue.fields.status.name}*] : {issue.fields.summary}",
                    }
                },
            ]
        }
    }

if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
