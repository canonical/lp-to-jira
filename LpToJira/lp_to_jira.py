#!/usr/bin/python3
# The purpose of lp-to-jira is to take a launchad bug ID and
# create a new Entry in JIRA in a given project


import argparse
import json
import os
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

    modified_since = None

    if days:
        modified_since = (datetime.now() - timedelta(days)).strftime('%Y-%m-%d')

    bug_tasks = lp_project.searchTasks(
        modified_since=modified_since,
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

def get_all_lp_merge_proposals(lp, project, reviewers):
    """Return list of merge proposals for the specified reviewers and project."""

    lp_user = lp.people["cjwatson"]
    print(lp_user)

    for b in lp_user.getBranches():
        print(b)

    return None

    merge_proposals = []

    try:
        lp_project = lp.projects[project]
    except KeyError:
        print("Couldn't find the Launchpad project \"{}\"".format(project))
        return None

    mps = lp_project.getMergeProposals(
        status=[
            'Work in progress',
            'Needs review',
            'Approved',
            'Merged',
            'Code failed to merge',
            'Queued',
            'Superseded'
            ]
        )

    for mp in mps:
        for vote in mp.votes_collection:
            if vote.reviewer.name in reviewers:
                print(project, mp, mp.queue_status, vote.reviewer.name)

    return None

def is_bug_in_jira(jira, bug, project_id):
    """Checks Jira for the same ID as the Bug you're trying to import"""

    issues = jira.search_issues(
        "project = \"{}\" AND summary ~ \"LP#{}\"".format(project_id, bug.id))

    if issues:
        print("Launchpad Issue {} is already logged "
              "in JIRA here {}/browse/{}".format(
                  bug.id,
                  jira.client_info(),
                  issues[0].key))
        return True, issues[0]
    return False, None

def get_first_matching_assignee(bug, assignees):
    """Return the first assignee and status matching an entry in assignees"""
    if len(assignees) > 0:
        for serie in bug.bug_tasks:
            if serie.assignee and (serie.assignee.name in assignees):
                return serie.assignee.name, serie.status
 
    return None, None



def update_bug_in_jira(jira, bug, issue, assignees, user_map, status_map, dry_run=False):
    """Update Jira status fields from Launchpad Bug"""

    assignee, status = get_first_matching_assignee(bug, assignees)
    if status:
        status = status_map[status]
    else:
        # If no assignee maps, set issue to complete
        status = "Done"

    lp_state = { "assignee": user_map.get(assignee), "status": status }
    jira_assignee = issue.fields.assignee.accountId if issue.fields.assignee else None
    jira_state = { "assignee": jira_assignee, "status": issue.fields.status.name }

    if lp_state != jira_state:
        print("Updating {} from {} -> {}".format(issue.key, jira_state, lp_state))
        if not dry_run:
            fields = {"assignee": {"accountId": lp_state["assignee"]}}
            jira.transition_issue(issue, transition=status)

def build_jira_issue(lp, bug, project_id, issue_type, assignee, component, opts=None):
    """Builds and return a dict to create a Jira Issue from"""

    # Get bug info from LP
    bug_pkg = get_lp_bug_pkg(bug)

    # Build the Jira Issue from the LP info
    issue_dict = {
        'project': project_id,
        'summary': 'LP#{} [{}] {}'.format(bug.id, bug_pkg, bug.title),
        'description': bug.description,
        'assignee': { 'accountId': opts.user_map[assignee]},
        'issuetype': {'name': issue_type}
    }

    # Only add component to the JIRA issue if it there's an acual component
    if component:
        issue_dict["components"] = [{"name": component}]

    return issue_dict


def create_jira_issue(jira, issue_dict, bug, opts=None):
    """Create and return a Jira Issue from issue_dict"""

    # Import the bug and return the JIRA ID for said bug
    new_issue = jira.create_issue(fields=issue_dict)

    # Adding a link to the Launchpad bug into the JIRA entry
    link = {'url': bug.web_link, 'title': 'Launchpad Link', 'icon': {'url16x16': 'https://bugs.launchpad.net/favicon.ico'}}
    jira.add_simple_link(new_issue, object=link)

    print("Created {}/browse/{}".format(jira.client_info(), new_issue.key))

    if opts and opts.epic:
        try:
            jira.add_issues_to_epic(opts.epic, [new_issue.id])
            print("Added to Epic %s" % opts.epic)
        except JIRAError as err:
            print("Failed to add to Epic {0}:\n{1}".format(opts.epic, err))

    return new_issue


def lp_to_jira_bug(lp, jira, bug, sync, opts):
    """Create JIRA issue at project_id for a given Launchpad bug"""

    project_id = sync["jira_project"]
    assignees = list(opts.user_map.keys())
    assignee = None
    status = None

    exists, issue = is_bug_in_jira(jira, bug, project_id)
    if exists:
        update_bug_in_jira(jira, bug, issue, assignees, opts.user_map, opts.status_map, opts.dry_run)
        return

    sync_to_jira = False

    if len(assignees) == 0:
        # If no assignees specified, sync everything
        sync_to_jira = True
    else:
        assignee, status = get_first_matching_assignee(bug, assignees)
        sync_to_jira = True if assignee else False

    if not sync_to_jira:
        return

    issue_type = sync.get("issue_type", "Bug")
    component = sync.get("component", None)
    issue_dict = build_jira_issue(lp, bug, project_id, issue_type, assignee, component, opts)
    if opts.label:
        # Add labels if specified
        issue_dict["labels"] = [opts.label]

    if opts.dry_run:
        print("(dry-run) Creating JIRA issue {}".format(issue_dict))
    else:
        jira_issue = create_jira_issue(jira, issue_dict, bug, opts)

    if opts.lp_link:
       if opts.dry_run:
           print("(dry-run) Adding JIRA issue link to bug description")
       else:
           # Add reference to the JIRA entry in the bugs on Launchpad
           bug.description += '\n\n---\nExternal link: https://warthogs.atlassian.net/browse/'+str(jira_issue.key)
           bug.lp_save()

    if not opts.no_lp_tag:
        if opts.dry_run:
            print("(dry-run) Adding JIRA issue ID to bug tags")
        else:
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
        '--add-link-in-lp-desc',
        dest='lp_link',
        action='store_true',
        help='Add JIRA link in LP Bug description'
    )
    opt_parser.add_argument(
        '--no-lp-tag',
        dest='no_lp_tag',
        action='store_true',
        help='Do not add tag to LP Bug'
    )
    opt_parser.add_argument(
        '--merge-proposals',
        dest='merge_proposals',
        action='store_true',
        help='Only query merge proposals'
    )
    opt_parser.add_argument(
        '--dry-run',
        dest='dry_run',
        action='store_true',
        default=False,
        help='Dry run, make no changes'
    )
    opt_parser.add_argument(
            '--config-json',
            dest='config',
            type=argparse.FileType('r'),
            help='JSON configuration file')

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

    opts.status_map = {}
    opts.user_map = {}
    opts.sync_project = []

    if opts.config:
        json_config = json.load(opts.config)
        opts.sync_project = json_config["project"]
        opts.status_map = json_config["status_map"]
        opts.user_map = json_config["user_map"]
    elif opts.sync_project_bugs:
        sync_project = {"launchpad_project": opts.sync_project_bugs, "jira_project": opts.project, "assignees": None}
        opts.sync_project.append(sync_project)

    # Ensure unassigned user maps
    opts.user_map[None] = None

    if opts.merge_proposals:
        reviewers = list(opts.user_map.keys())
        for project in opts.sync_project:
            merge_proposals = get_all_lp_merge_proposals(lp, project["launchpad_project"], reviewers)

        return 0

    # Iterate over project list
    for sync in opts.sync_project:
        tasks_list = get_all_lp_project_bug_tasks(
            lp, sync["launchpad_project"], opts.days, opts.tags)
        if tasks_list is None:
            continue

        for bug_task in tasks_list:
            bug = bug_task.bug
            lp_to_jira_bug(lp, jira, bug, sync, opts)

    if len(opts.sync_project) > 0:
        # Stop here if any project sync was specified
        return 0

    bug_number = opts.bug
    project_id = opts.project
    config = {"jira_project": project_id}

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
    lp_to_jira_bug(lp, jira, bug, config, opts)

    return 0

if __name__ == "__main__":
    main()
