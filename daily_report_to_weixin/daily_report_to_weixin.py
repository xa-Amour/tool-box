import glob
import json
import time
import xml.dom.minidom
from collections import Counter
from optparse import OptionParser

import requests

parser = OptionParser()
parser.add_option("-r", "--report_folder", action="store", dest="report_folder",
                  help="directory of report to be parsed")
parser.add_option("-b", "--target_branch", action="store", dest="target_branch",
                  help="smoke test branch")
parser.add_option("-p", "--platform", action="store", dest="platform",
                  help="smoke test platform")
parser.add_option("-u", "--url", action="store", dest="url",
                  help="url for enterprise WeChat")
parser.add_option("-a", "--admin", action="store", dest="admin",
                  help="admin of jenkins")
parser.add_option("-w", "--password", action="store", dest="password",
                  help="password of admin")
parser.add_option("-j", "--job_name", action="store", dest="job_name",
                  help="smoke test job name")
parser.add_option("-c", "--crash_build_number_str", action="store", dest="crash_build_number_str", default="",
                  help="crash build number string gather")
(options, _) = parser.parse_args()

failure_case_combination = []
crash_case_combination = []


def handle_single_report(report_file):
    dom = xml.dom.minidom.parse(report_file)
    root = dom.documentElement
    if not root.getElementsByTagName("failure"):
        return
    for node in (node for node in root.getElementsByTagName("testcase") if
                 any(child_node for child_node in node.childNodes if child_node.nodeName == 'failure')):
        failure_class_name = node.getAttribute("classname")
        failure_test_case = node.getAttribute("name")
        failure_case_combination.append(
            failure_class_name + '.' + failure_test_case)


def handle_crash_condition(admin, password, job_name, crash_build_number):
    global crash_case_combination
    run_wait = False
    if_has_crash_lst = []
    if not crash_build_number:
        return
    res = requests.get(
        'http://{admin}:{password}@<jenkins_job_url_placeholder>/{job_name}/{crash_build_number}/consoleText'.format(
            admin=admin, password=password, job_name=job_name, crash_build_number=crash_build_number))
    assert res.status_code == 200
    for run_case in res.text.split('\n'):
        if "DISABLED" in run_case:
            continue
        if "[ RUN      ]" in run_case:
            run_wait = True
            doubtful_crash_case = run_case.split()[-1]
            if_has_crash_lst.append(doubtful_crash_case)
        if run_wait and ("[  FAILED  ]" in run_case):
            failure_case_combination.append(doubtful_crash_case)
        if run_wait and ("[       OK ]" in run_case or "[  FAILED  ]" in run_case):
            run_wait = False
            if_has_crash_lst.pop()
    crash_case_combination += if_has_crash_lst


def send_report_to_weixin(report_folder, target_branch, platform, url, admin, password, job_name,
                          crash_build_number_str):
    failure_cases_info = ''
    crash_cases_info = ''
    gen_report_date = time.strftime("%Y-%m-%d", time.localtime())
    for file in glob.glob("{report_folder}/*.xml".format(report_folder=report_folder)):
        handle_single_report(file)

    for crash_build_number in crash_build_number_str.split():  # Convert the string argument received by OptionParser into list type
        handle_crash_condition(admin, password, job_name, crash_build_number)

    failure_case_count = len(Counter(failure_case_combination))
    for key, value in Counter(failure_case_combination).items():
        failure_cases_info += "{key} : {value} time(s) \n".format(key=key, value=str(value))

    crash_case_count = len(Counter(crash_case_combination))
    for key, value in Counter(crash_case_combination).items():
        crash_cases_info += "{key} : {value} time(s) \n".format(key=key, value=str(value))
    
    info_template = "**Smoke_Test_{target_branch}_{platform}_{gen_report_date}** \n"
    success_template = "<font color=\"info\"> All PASSED </font>"
    failure_template = "Failed Cases: <font color=\"warning\">{failure_case_count}</font> \n {failure_cases_info}"
    crash_template = "Crash Cases: <font color=\"warning\">{crash_case_count}</font> \n {crash_cases_info}"
    send_info = info_template.format(target_branch=target_branch, platform=platform, gen_report_date=gen_report_date)

    if not failure_cases_info and not crash_cases_info: send_info += success_template
    if failure_cases_info: send_info += failure_template.format(failure_case_count=failure_case_count,
                                                                failure_cases_info=failure_cases_info)
    if crash_cases_info: send_info += crash_template.format(crash_case_count=crash_case_count,
                                                            crash_cases_info=crash_cases_info)

    payload = {
        "msgtype": "markdown",
        "agentid": 1,
        "markdown": {
            "content": send_info
        },
        "safe": 0,
        "enable_id_trans": 0,
        "enable_duplicate_check": 0
    }
    requests.post(url, data=json.dumps(payload))


def main():
    send_report_to_weixin(
        report_folder=options.report_folder,
        target_branch=options.target_branch,
        platform=options.platform,
        url=options.url,
        admin=options.admin,
        password=options.password,
        job_name=options.job_name,
        crash_build_number_str=options.crash_build_number_str
    )


if __name__ == '__main__':
    main()