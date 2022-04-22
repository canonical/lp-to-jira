#!/usr/bin/python3
# The purpose of lp-to-jira is to take a launchad bug ID and
# create a new Entry in JIRA in a given project


import sys
import json
import datetime

from optparse import OptionParser

from launchpadlib.launchpad import Launchpad
from jira import JIRA
from LpToJira.jira_api import jira_api


jira_server = ""
jira_project = ""

db_json = "lp_to_jira_db.json"

def get_bug_id(summary):
    "Extract the bug id from a jira title which would include LP#"
    id = ""

    if "LP#" in summary:
        for char in summary[summary.find("LP#")+3:]:
            if char.isdigit():
                id = id + char
            else:
                break

    return id

def build_db(jira_api, lp_api, project):
    # structure that contains all the LP/JIRA issues pair as well as the latest
    # time it was modified in LP
    db = {}

    # 3.a search for all JIRA issues that starts with LP#
    print("Searching for JIRA issues ...", flush=True)
    # Get JIRA issues in batch of 50

    issue_index = 0
    issue_batch = 50

    while True:
        start_index = issue_index * issue_batch
        request = "project = {} " \
            "AND summary ~ \"LP#\" " \
            "AND status in (BLOCKED, Backlog, \"In Progress\", " \
            "REVIEW,\"Selected for Development\")""".format(project)
        issues = jira_api.search_issues(request, startAt=start_index)

        if not issues:
            break

        issue_index += 1
        for issue in issues:
            print("#", flush=True, end="")
            summary = issue.fields.summary
            lpbug_id = get_bug_id(summary)
            try:
                lpbug = lp_api.bugs[int(lpbug_id)]
                db[lpbug_id] = {'JIRA_KEY' : issue.key,
                    'LAST_CHANGE':"%s" % lpbug.date_last_updated}
            except Exception:
                pass

    return db

def main():
    global jira_server
    usage = """\
usage: lp-to-jira-monitor project-id

Examples:
    lp-to-jira-monitor FR
    """
    opt_parser = OptionParser(usage)
    opts, args = opt_parser.parse_args()

    # # Make sure there's at least 1 arguments
    if len(args) < 1:
        opt_parser.print_usage()
        return 1


    jira_project = args[0]

    # 1. Initialize JIRA API
    print("Initialize JIRA API ...")
    api = jira_api()
    jira_server = api.server
    jira = JIRA(api.server, basic_auth=(api.login, api.token))

    # TODO: catch exception if the Launchpad API isn't open
    # 2. Initialize Launchpad API
    print("Initialize Launchpad API ...")
    lp = Launchpad.login_with('foundations', 'production', version='devel')

    try:
        with open(db_json) as fp:
            jira_lp_db = json.load(fp)
        # TODO: check if there's new entry in JIRA that need to be added to the DB
        # refresh_db(jira, lp, jira_project, jira_lp_db)
    except (FileNotFoundError):
        jira_lp_db = build_db(jira, lp, jira_project)

    print("\nFound %s issues" % len(jira_lp_db))
    # Saving DB to disk
    with open(db_json, 'w') as fp:
            json.dump(jira_lp_db, fp, indent=2)

    has_changed = False
    while not has_changed:
        print("Searching for changes %s" % datetime.datetime.now())
        for bug in jira_lp_db:
            try:
                old_date = jira_lp_db[bug]['LAST_CHANGE']
                current_date = "%s" % lp.bugs[int(bug)].date_last_updated
                if  current_date!= old_date:
                    has_changed = True
                    print("%s has changed since last refresh" % bug)
                    # TODO: compare issues and update JIRA item accordingly
                    # TODO: then replace date in db
                    # TODO: We could think of policy allowing to only update certain field like description, title

            except Exception:
                pass

    return 0

main()

