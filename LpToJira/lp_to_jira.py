#!/usr/bin/python3
# The purpose of lp-to-jira is to take a launchad bug ID and
# create a new Entry in JIRA in a given project


import sys
import os
import json

from optparse import OptionParser
from datetime import datetime, timedelta

from launchpadlib.launchpad import Launchpad
from launchpadlib.credentials import UnencryptedFileCredentialStore

from jira import JIRA
from LpToJira.jira_api import jira_api


# TODO: paramaterize this, for now we just hardcode
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
    "ubuntu-release-upgrader": "Package Management",
    "solutions-qa-ci": "Solutions QA CI",
    "cpe-foundation": "FCE",
}
default_component = "Distro"


def get_lp_bug(lp, bug_number):
    """Make sure the bug ID exists, return bug"""

    bug = None
    try:
        bug = lp.bugs[bug_number]
    except Exception:
        print("Couldn't find the Launchpad bug {}".format(bug_number))
        sys.exit(1)

    return bug


def get_lp_bug_pkg(lp, bug):
    """From a LP bug, get its package"""

    bug_pkg = None
    if len(bug.bug_tasks) == 1:
        bug_pkg = bug.bug_tasks[0].bug_target_name.split()[0]
    else:
        for task in bug.bug_tasks:
            if "(Ubuntu)" in task.bug_target_name:
                bug_pkg = task.bug_target_name.split()[0]

    return bug_pkg


def get_all_lp_project_bugs(lp, project, days=None):
    """Return iterable IBugTasks of all Bugs in a Project filed in the past n
    days. If days is not specified, return all Bugs."""

    try:
        lp_project = lp.projects[project]
    except KeyError:
        print("Couldn't find the Launchpad project \"{}\"".format(project))
        sys.exit(1)

    created_since = None

    if days:
        created_since = (datetime.now() - timedelta(days)).strftime('%Y-%m-%d')

    bugs = lp_project.searchTasks(
        created_since=created_since,
        status=[
            'New',
            'Incomplete',
            'Triaged',
            'Opinion',
            'Invalid',
            'Won\'t Fix',
            'Confirmed',
            'In Progress',
            'Fix Committed',
            'Fix Released'
        ])

    return bugs


def is_bug_in_jira(jira, bug, project_id):
    """Checks Jira for the same ID as the Bug you're trying to import"""

    existing_issue = jira.search_issues(
        "project = \"{}\" AND summary ~ \"LP#{}\"".format(project_id, bug.id))

    if existing_issue:
        print("Launchpad Issue {} is already logged "
              "in JIRA here {}/browse/{}".format(
                  bug.id,
                  jira.client_info(),
                  existing_issue[0].key))
        return True
    return False


def build_jira_issue(lp, bug, project_id):
    """Builds and return a dict to create a Jira Issue from"""

    # Get bug info from LP
    bug_pkg = get_lp_bug_pkg(lp, bug)

    # Build the Jira Issue from the LP info
    issue_dict = {
        'project': project_id,
        'summary': 'LP#{} [{}] {}'.format(bug.id, bug_pkg, bug.title),
        'description': bug.description,
        'issuetype': {'name': 'Bug'}
    }

    jira_component = []
    jira_component.append(
        {"name":pkg_to_component.get(bug_pkg, default_component)})
    issue_dict["components"] = jira_component
    
    return issue_dict


def create_jira_issue(jira, issue_dict, bug):
    """Create and return a Jira Issue from issue_dict"""

    # Import the bug and return the JIRA ID for said bug
    new_issue = jira.create_issue(fields=issue_dict)

    # Adding a link to the Launchpad bug into the JIRA entry
    link = {'url': bug.web_link, 'title': 'Launchpad Link'}
    jira.add_simple_link(new_issue, object=link)

    print("Created {}/browse/{}".format(jira.client_info(), new_issue.key))

    return new_issue


def lp_to_jira_bug(lp, jira, bug, project_id, opts):
    """Create JIRA issue at project_id for a given Launchpad bug"""
    
    if is_bug_in_jira(jira, bug, project_id):
        return
    
    issue_dict = build_jira_issue(lp, bug, project_id)
    if opts.label:
        # Add labels if specified
        issue_dict["labels"] = [opts.label]

    jira_issue = create_jira_issue(jira, issue_dict, bug)

    if not opts.no_lp_tag:
        # Add reference to the JIRA entry in the bugs on Launchpad
        bug.tags += [jira_issue.key.lower()]
        bug.lp_save()


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
    -s SYNC_PROJECT_BUGS, --sync_project_bugs=SYNC_PROJECT_BUGS
                The name of the LP Project. This will bring in every
                bug from your project if you do not also specify days
    -d DAYS, --days=DAYS
                Only look for LP Bugs in the past n days
    --no-lp-tag

Examples:
    lp-to-jira 3215487 FR
    lp-to-jira -e 3215487 FR
    lp-to-jira -l ubuntu-meeting 3215487 PR
    lp-to-jira -s ubuntu -d 3 IQA
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

    opt_parser.add_option(
        '-s', '--sync_project_bugs',
        dest='sync_project_bugs',
        action='store',
        type=str,
        help='Adds all bugs from a specified LP Project to specified Jira board'
            ' if they are not already on the Jira board.'
            ' Use --days to narrow down bugs'
    )

    opt_parser.add_option(
        '-d', '--days',
        dest='days',
        action='store',
        type=int,
        help='Only look for LP Bugs in the past n days'
    )

    opt_parser.add_option(
        '--no-lp-tag',
        dest='no_lp_tag',
        action='store_true',
        help='Do not add tag to LP Bug'
    )

    opts, args = opt_parser.parse_args()

    # Connect to Launchpad API
    # TODO: catch exception if the Launchpad API isn't open
    credential_store = UnencryptedFileCredentialStore(os.path.expanduser("~/.lp_creds"))
    lp = Launchpad.login_with(
        'foundations',
        'production',
        version='devel',credential_store=credential_store)

    # Connect to the JIRA API
    api = jira_api()
    jira = JIRA(api.server, basic_auth=(api.login, api.token))

    if opts.sync_project_bugs:
        bugs_list = get_all_lp_project_bugs(lp, opts.sync_project_bugs, opts.days)

        for bug in bugs_list:
            bug_number = bug.bug_link.split('/')[-1]
            bug = get_lp_bug(lp, bug_number)
            lp_to_jira_bug(lp, jira, bug, args[0], opts)
        return 0

    # Make sure there's 2 arguments
    if len(args) < 2:
        opt_parser.print_usage()
        return 1

    bug_number = args[0]
    project_id = args[1]
    bug = get_lp_bug(lp, bug_number)

    if opts.exists:
        # We are simply testing if the bug was already in JIRA
        if is_bug_in_jira(jira, bug, project_id):
            return 0
        print("Launchpad Issue {} is not in JIRA project {}".format(
            bug.id, project_id))
        return 1

    # Create the Jira Issue
    lp_to_jira_bug(lp, jira, bug, project_id, opts)

    return 0
