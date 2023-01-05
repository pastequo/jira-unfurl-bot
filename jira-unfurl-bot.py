import os
import jira
from jira.resources import Version

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
ISSUE_TYPE_TO_ICON = {
    "Epic": "jiraepic",
    "Bug": "jirabug",
    "Task": "jiratask",
    "Story": "jirastory",
}
ISSUE_TYPE_TO_PRIORITY = {
    "Epic": 1,
    "Bug": 2,
    "Story": 3,
    "Task": 4,
}
MAX_SHOWN_ISSUES_IN_VERSION = 10


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

        client.chat_unfurl(
            channel=payload["channel"],
            ts=payload["message_ts"],
            unfurls=_payload,
        )


def get_version_payload(version: Version, url: str):
    release_info = f"Released at {version.releaseDate}" if version.released else "Unreleased"

    text = f":jira: *{version.name}* [*{release_info}*]"

    description = version.raw.get("description")
    if description is not None:
        text += f" : {description}"

    jql_filter = f'project = {version.projectId} AND fixVersion = "{version.name}"'
    if jira_client.version_count_related_issues(version.id)["issuesFixedCount"] > MAX_SHOWN_ISSUES_IN_VERSION:
        # if too much issues are linked to the version, show only bugs and epics
        jql_filter += " AND issuetype in (Bug, Epic)"

    linked_issues = jira_client.search_issues(jql_str=jql_filter)
    linked_issues.sort(key=lambda issue: ISSUE_TYPE_TO_PRIORITY[issue.fields.issuetype.name])

    for issue in linked_issues[:MAX_SHOWN_ISSUES_IN_VERSION]:
        icon = ISSUE_TYPE_TO_ICON.get(issue.fields.issuetype.name, "jira-1992")
        text += f"\n\t\t:{icon}: <{issue.permalink()}|{issue.fields.summary}>"

    if len(linked_issues) > MAX_SHOWN_ISSUES_IN_VERSION:
        text += f"\n\t\t... ({len(linked_issues) - MAX_SHOWN_ISSUES_IN_VERSION} more epics/bugs to show. <{url}|See more>)"

    return {
        url: {
            "color": "#ff8b3d",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text,
                    }
                },
            ],
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
