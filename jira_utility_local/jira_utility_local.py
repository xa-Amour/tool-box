import base64
import json
import logging
import pprint
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AUTH = HTTPBasicAuth(
    base64.b64decode('usernameb64encode'),
    base64.b64decode('passwordb64encode'))

jira_matrix = {
    "feature1_branch": {"assignee": {"linux": "linux_owner", "windows": "windows_owner"},
                        "main_issue_id": {"linux": "MS-1", "windows": "MS-2"},
                        "if_subtask": {"is_subtask": {"parent_id": {"linux": "10XXX", "windows": "10XXX"}},
                                       "non_subtask": "10002"
                                       }
                        },
    "feature2_branch": {"assignee": {"linux": "linux_owner", "windows": "windows_owner"},
                        "main_issue_id": {"linux": "MS-3", "windows": "MS-4"},
                        "if_subtask": {"is_subtask": {"parent_id": {"linux": "10XXX", "windows": "10XXX"}},
                                       "non_subtask": "10002"
                                       }
                        },
    "feature3_branch": {"assignee": {"linux": "linux_owner", "windows": "windows_owner"},
                        "main_issue_id": {"linux": "MS-5", "windows": "MS-6"},
                        "if_subtask": {"is_subtask": {"parent_id": {"linux": "10XXX", "windows": "10XXX"}},
                                       "non_subtask": "10002"
                                       }
                        },
    "feature4_branch": {"assignee": {"linux": "linux_owner", "windows": "windows_owner"},
                        "main_issue_id": {"linux": "MS-7", "windows": "MS-8"},

                        "if_subtask": {"is_subtask": {"parent_id": {"linux": "10XXX", "windows": "10XXX"}},
                                       "non_subtask": "10002"
                                       }
                        },
}


def get_token():
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"grant_type": "password",
               "client_id": "clinet_id_encode",
               "client_secret": "client_secret_encode",
               "username": "username_encode",
               "password": "password_encode"}
    res = requests.post(
        "https://oauth.companylab.co/oauth/token",
        data=payload,
        headers=headers)
    if res.status_code != 200:
        logger.warning(
            "Failed to get token && Status code:{}".format(
                res.status_code))
    access_token = json.loads(res.content).get("access_token")
    return access_token


def get_headers():
    headers = {
        "accessToken": get_token(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    return headers


class JiraConnection(object):
    def query(self, issue_id):
        res = requests.get(
            "https://jira.companylab.co/rest/api/2/issue/" +
            issue_id,
            headers=get_headers(),
            auth=AUTH)
        return res.json()

    def attachment_to_description(self, attachment):
        case_name = attachment["filename"]
        issue_url = attachment["content"]
        res = requests.get(issue_url, headers=get_headers(), auth=AUTH)
        url = res.text.split('\n')[0]
        description = "[ {case_name} ] failed or crash \n\n Please click on the URL for more information : \n\n {url}".format(
            case_name=case_name, url=url)
        return description

    def create_issue(
            self,
            summary,
            description,
            fixVersions,
            versions,
            os,
            assignee):
        if len(description) >= 32767:
            description = description[0:32700]
        payload = {
            "fields": {
                "summary": summary,
                "components": [
                    {
                        "self": "https://jira.companylab.co/rest/api/2/component/104xx",
                        "id": "104xx",
                        "name": "SDK",
                        "description": "Issues Related to This Project "
                    }
                ],
                "project": {
                    "self": "https://jira.companylab.co/rest/api/2/project/12xxx",
                    "id": "12xxx",
                    "key": "MS",
                    "name": "Main Pro",
                },
                "customfield_10700": os,
                "description": description,
                "fixVersions": fixVersions,
                "priority": {
                    "self": "https://jira.companylab.co/rest/api/2/priority/2",
                    "iconUrl": "https://jira.companylab.co/images/icons/priorities/critical.svg",
                    "name": "High",
                    "id": "2"
                },
                "labels": [
                    "UT"
                ],
                "timetracking": {},
                "versions": versions,
                "issuetype": {
                    "id": "10004",
                    # 10004 issuetype is bug; 10003 issuetype is task 并且前面需要有
                    # parent_id; 10002 issuetype is task 并且前面不能有 parent_id
                },
                "customfield_11621": {
                    "self": "https://jira.companylab.co/rest/api/2/customFieldOption/112xx",
                    "value": "可用性（Availability）",
                    "id": "112xx"
                },
                "assignee": assignee
            }
        }
        res = requests.post(
            "https://jira.companylab.co/rest/api/2/issue",
            headers=get_headers(),
            data=json.dumps(payload),
            auth=AUTH)
        if res.status_code >= 200 and res.status_code <= 299:
            issue_id = json.loads(res.content).get("key")
            logger.info("Success to create issue:[{}] ".format(issue_id))
            return issue_id
        else:
            logger.error(
                "Create issue failed && Status code:{}".format(
                    res.status_code))

    def link_issue(self, main_issue_id, sub_issue_id):
        payload = {
            "type": {
                "name": "Duplicate"
            },
            "inwardIssue": {
                "key": sub_issue_id
            },
            "outwardIssue": {
                "key": main_issue_id
            }
        }
        res = requests.post(
            "https://jira.companylab.co/rest/api/2/issueLink",
            headers=get_headers(),
            data=json.dumps(payload),
            auth=AUTH)
        if res.status_code >= 200 and res.status_code <= 299:
            logger.info(
                "Link sub issue [{}] to main [{}] success".format(
                    sub_issue_id, main_issue_id))
        else:
            logger.error(
                "Link issue to [{}] failed && Status code:{}".format(
                    main_issue_id, res.status_code))


class JiraMainTask(object):
    def __init__(self):
        self.os = ""
        self.summary = ""
        self.fixVersions = []
        self.versions = []
        self.jiraConnection = JiraConnection()

    def query(self, issue_id):
        jiraInfo = self.jiraConnection.query(issue_id)
        self.mainIssueId = issue_id
        self.summary = jiraInfo['fields']['summary']
        self.fixVersions = jiraInfo['fields']['fixVersions']
        self.versions = jiraInfo['fields']['versions']
        self.attachment = jiraInfo['fields']['attachment']
        self.assignee = jiraInfo['fields']['assignee']
        self.os = jiraInfo['fields']['customfield_10700']

    def create_subtasks(self):
        for elem in self.attachment:
            self.create_subtask(
                elem["filename"],
                self.jiraConnection.attachment_to_description(elem))

    def create_subtask(self, case_name, description):
        summary = "[{os} UT Fail] {case_name}".format(
            os=self.get_summary_os(), case_name=case_name)
        inwardIssue = self.jiraConnection.create_issue(
            summary, description, self.fixVersions, self.versions, self.os, self.assignee)
        self.jiraConnection.link_issue(self.mainIssueId, inwardIssue)

    def get_summary_os(self):
        if self.os:
            return self.os[0].get("value")


def main():
    issues_lst = [
        'MS-2xxxx',
    ]
    for issue_id in issues_lst:
        jiraMainTask = JiraMainTask()
        jiraMainTask.query(issue_id)
        jiraMainTask.create_subtasks()


if __name__ == '__main__':
    main()
