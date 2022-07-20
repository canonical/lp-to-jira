#!/usr/bin/python3
# The purpose of lp-to-jira is to take a launchad bug ID and
# create a new Entry in JIRA in a given project


import os
import argparse
import textwrap

from datetime import datetime, timedelta

from launchpadlib.launchpad import Launchpad
from launchpadlib.credentials import UnencryptedFileCredentialStore

from jira import JIRA, JIRAError
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
    "fce-templates": "FCE Templates",
}


def get_lp_bug(lp, bug_number):
    """Make sure the bug ID exists, return bug"""

    bug = None

    if lp is None:
        return bug

    try:
        bug = lp.bugs[bug_number]

    except KeyError:
        print("Couldn't find the Launchpad bug {}".format(bug_number))

    return bug


def get_lp_bug_pkg(bug):
    """
    From a LP bug, get its package
    a Launchpad bug may impact multiple packages,
    this function is pretty unprecise as it returns only the latest package
    TODO: probably do something about this, return a list or fail if multiple
    packages.
    """

    bug_pkg = None

    # Only return bug from Ubuntu (will return the last one if multiple pkgs
    for task in bug.bug_tasks:
        if "(Ubuntu" in task.bug_target_name:
            bug_pkg = task.bug_target_name.split()[0]

    return bug_pkg


def get_all_lp_project_bug_tasks(lp, project, days=None, tags=None):
    """Return iterable IBugTasks of all Bugs in a Project filed in the past n
    days. If days is not specified, return all Bugs."""

    try:
        lp_project = lp.projects[project]
    except KeyError:
        print("Couldn't find the Launchpad project \"{}\"".format(project))
        return None

    created_since = None

    if days:
        created_since = (datetime.now() - timedelta(days)).strftime('%Y-%m-%d')

    bug_tasks = lp_project.searchTasks(
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
        ],
        tags=tags
    )

    return bug_tasks


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


def build_jira_issue(lp, bug, project_id, opts=None):
    """Builds and return a dict to create a Jira Issue from"""

    # Get bug info from LP
    bug_pkg = get_lp_bug_pkg(bug)

    # Build the Jira Issue from the LP info
    issue_dict = {
        'project': project_id,
        'summary': 'LP#{} [{}] {}'.format(bug.id, bug_pkg, bug.title),
        'description': bug.description,
        'issuetype': {'name': 'Bug'}
    }

    if opts and opts.component:
        jira_component = [{"name": opts.component}]
    else:
        jira_component = [
            {"name": pkg_to_component.get(bug_pkg)}
        ]
    issue_dict["components"] = jira_component

    return issue_dict


def create_jira_issue(jira, issue_dict, bug, opts=None):
    """Create and return a Jira Issue from issue_dict"""

    # Import the bug and return the JIRA ID for said bug
    new_issue = jira.create_issue(fields=issue_dict)

    # Adding a link to the Launchpad bug into the JIRA entry
    link = {'url': bug.web_link, 'title': 'Launchpad Link'}
    jira.add_simple_link(new_issue, object=link)

    print("Created {}/browse/{}".format(jira.client_info(), new_issue.key))

    if opts and opts.epic:
        try:
            jira.add_issues_to_epic(opts.epic, [new_issue.id])
            print("Added to Epic %s" % opts.epic)
        except JIRAError as err:
            print("Failed to add to Epic {0}:\n{1}".format(opts.epic, err))

    return new_issue


def lp_to_jira_bug(lp, jira, bug, project_id, opts):
    """Create JIRA issue at project_id for a given Launchpad bug"""

    if is_bug_in_jira(jira, bug, project_id):
        return

    issue_dict = build_jira_issue(lp, bug, project_id, opts)
    if opts.label:
        # Add labels if specified
        issue_dict["labels"] = [opts.label]

    jira_issue = create_jira_issue(jira, issue_dict, bug, opts)

    if not opts.no_lp_tag:
        # Add reference to the JIRA entry in the bugs on Launchpad
        bug.tags += [jira_issue.key.lower()]
        bug.lp_save()


def main(args=None):
    opt_parser = argparse.ArgumentParser(
        description="A script create JIRA issue from Launchpad bugs",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent('''\
        Examples:
            lp-to-jira 3215487 FR
            lp-to-jira -e 3215487 FR
            lp-to-jira -l ubuntu-meeting 3215487 PR
            lp-to-jira -s ubuntu -d 3 IQA
            lp-to-jira --no-lp-tag -c Network -E FS-543 123231 PR
            lp-to-jira -s ubuntu -t go-to-jira PR
            lp-to-jira -s ubuntu -t go-to-jira -t also-to-jira PR
            lp-to-jira -s ubuntu -t=-ignore-these PR
        ''')
    )
    opt_parser.add_argument(
        'bug', type=int,
        # Somewhat hacky way to allow -s option to not require bug id
        # -s (sync) is an optional parameter that doesn't require bug id
        default=0,
        nargs='?',
        help="The Launchpad numeric bug ID")
    opt_parser.add_argument(
        'project', type=str,
        help="The JIRA project string key")
    opt_parser.add_argument(
        '-l',
        '--label',
        dest='label',
        help='Add LABEL to the JIRA issue after creation')
    opt_parser.add_argument(
        '-c',
        '--component',
        dest='component',
        help='Specify COMPONENT to assign the issue to')
    opt_parser.add_argument(
        '-E',
        '--epic',
        dest='epic',
        help='Specify EPIC to link this new issue to')
    opt_parser.add_argument(
        '-e', '--exists',
        dest='exists',
        action='store_true',
        help=textwrap.dedent('''
            Look if the Launchpad Bug has already been imported
            print the JIRA issue ID if found
        ''')
    )
    opt_parser.add_argument(
        '-s', '--sync_project_bugs',
        dest='sync_project_bugs',
        action='store',
        type=str,
        help=textwrap.dedent('''
            Adds all bugs from a specified LP Project to specified Jira board
            if they are not already on the Jira board.
            Use --days to narrow down bugs
            ''')
    )
    opt_parser.add_argument(
        '-d', '--days',
        dest='days',
        action='store',
        type=int,
        help='Only look for LP Bugs in the past n days'
    )
    opt_parser.add_argument(
        '-t', '--tag',
        dest='tags',
        action='append',
        type=str,
        help=textwrap.dedent('''
            Only look for LP Bugs with the specified tag(s). To exclude,
            prepend a '-', e.g. '-unwantedtag'
            ''')
    )
    opt_parser.add_argument(
        '--no-lp-tag',
        dest='no_lp_tag',
        action='store_true',
        help='Do not add tag to LP Bug'
    )

    opts = opt_parser.parse_args(args)

    if (opts.bug == 0 and not opts.sync_project_bugs):
        opt_parser.print_usage()
        print('lp-to-jira: error: the follow argument is required: bug')
        return 1

    # Connect to Launchpad API
    # TODO: catch exception if the Launchpad API isn't open
    snap_home = os.getenv("SNAP_USER_COMMON")
    if snap_home:
        credential_store = UnencryptedFileCredentialStore(
            "{}/.lp_creds".format(snap_home))
    else:
        credential_store = UnencryptedFileCredentialStore(
            os.path.expanduser("~/.lp_creds"))
    lp = Launchpad.login_with(
        'foundations',
        'production',
        version='devel', credential_store=credential_store)

    # Connect to the JIRA API
    try:
        api = jira_api()
    except ValueError:
        return "ERROR: Cannot initialize JIRA API."

    jira = JIRA(api.server, basic_auth=(api.login, api.token))

    if opts.sync_project_bugs:
        tasks_list = get_all_lp_project_bug_tasks(
            lp, opts.sync_project_bugs, opts.days, opts.tags)
        if tasks_list is None:
            return 1

        for bug_task in tasks_list:
            bug = bug_task.bug
            lp_to_jira_bug(lp, jira, bug, opts.project, opts)
        return 0

    bug_number = opts.bug
    project_id = opts.project

    bug = get_lp_bug(lp, bug_number)
    if bug is None:
        return 1

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
