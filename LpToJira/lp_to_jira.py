#!/usr/bin/python3
# The purpose of lp-to-jira is to take a launchad bug ID and
# create a new Entry in JIRA in a given project


import sys
import os
import json

from optparse import OptionParser

from launchpadlib.launchpad import Launchpad
from jira import JIRA
from LpToJira.jira_api import jira_api


pkg_to_component = {
    "nplan": "netplan",
    "netplan.io": "netplan",
    "netplan": "netplan",
    "systemd": "systemd",
    "s390-tools": "IBM",
    "subiquity": "subiquity",
    "curtin": "subiquity",
    "ubuntu-image": "Ubuntu Image",
    "shim-signed": "Secure Boot",
    "openjdk-lts": "OpenJDK",
    "apt": "Package Management",
    "aptdaemon": "Package Management",
    "ubuntu-release-upgrader": "Package Management"
}
default_component = "Distro"


def main():
    usage = """\
usage: lp-to-jira [options] bug-id project-id

Create JIRA entry for a given Launchpad bug ID

options:
    -e, --exists"
                Look if the Launchpad Bug has alreaady been imported
                print the JIRA issue ID if found
    -l, --label LABEL
                Add LABEL to the JIRA issue after creation

Examples:
    lp-to-jira 3215487 FR
    lp-to-jira -e 3215487 FR
    lp-to-jira -l ubuntu-meeting 3215487 PR
        """

    opt_parser = OptionParser(usage)
    opt_parser.add_option(
        '-l', '--label',
        dest='label',
    )
    opt_parser.add_option(
        '-e', '--exists',
        dest='exists',
        action='store_true'
    )

    opts, args = opt_parser.parse_args()

    # Make sure there's 2 arguments
    if len(args) < 2:
        opt_parser.print_usage()
        return 1

    bug_number = args[0]
    project_id = args[1]

    jira_token_file = "{}/.jira.token".format(os.path.expanduser('~'))

    # 1. Connect to Launchpad API

    # TODO: catch exception if the Launchpad API isn't open
    lp = Launchpad.login_with('foundations', 'production', version='devel')

    # 2. Make sure the bug ID exist
    bug = None
    bug_pkg = None
    try:
        bug = lp.bugs[bug_number]
    except Exception:
        print("Couldn't find the Launchpad bug {}".format(bug_number))
        return 1

    if len(bug.bug_tasks) == 1:
        bug_pkg = bug.bug_tasks[0].bug_target_name.split()[0]
    else:
        for task in bug.bug_tasks:
            if "(Ubuntu)" in task.bug_target_name:
                bug_pkg = task.bug_target_name.split()[0]

    # 3. Connect to the JIRA API
    api = jira_api()
    jira = JIRA(api.server, basic_auth=(api.login, api.token))

    # 4. Make sure that there's no bug in JIRA with the same ID
    # than the Bug you're trying to import
    existing_issue = jira.search_issues(
        "project = \"{}\" AND summary ~ \"LP#{}\"".format(project_id, bug.id))

    if existing_issue:
        print("Launchpad Issue {} is already logged "
              "in JIRA here {}/browse/{}".format(
                  bug_number,
                  api.server,
                  existing_issue[0].key))

        if opts.exists:
            # we are simply testing if the bug was already in JIRA
            # if it was we return 0
            return 0

        # However here the intent was to create a bug which already exists
        # So we return 1 instead
        return 1

    if opts.exists:
        print("Launchpad Issue {} is not in JIRA project {}".format(
            bug_number, project_id))
        return 1

    issue_dict = {
        'project': project_id,
        'summary': 'LP#{} [{}] {}'.format(bug.id, bug_pkg, bug.title),
        'description': bug.description,
        'issuetype': {'name': 'Bug'}
    }
    if opts.label:
        issue_dict["labels"] = [opts.label]

    jira_component = []
    jira_component.append(
        {"name":pkg_to_component.get(bug_pkg, default_component)})
    issue_dict["components"] = jira_component

    # 5. import the bug and return the JIRA ID for said bug
    new_issue = jira.create_issue(fields=issue_dict)

    # 6. Adding a link to the Launchpad bug into the JIRA entry
    link = {'url': bug.web_link, 'title': 'Launchpad Link'}
    jira.add_simple_link(new_issue, object=link)

    # 7. Add reference to the JIRA entry in the bugs on Launchpad
    bug.tags += [new_issue.key.lower()]
    bug.lp_save()

    print("Created {}/browse/{}".format(api.server, new_issue.key))

    return 0
