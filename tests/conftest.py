import pytest

from unittest.mock import Mock

from LpToJira.lp_bug import ubuntu_devel

@pytest.fixture
def lp_api():
    bug1 = Mock()
    bug1.title = "This is the title of a bug"
    bug1.description = "This is the longer description"
    bug1.heat = "100"
    bug1.importance = "Undecided"
    bug1.bug_tasks = [
        Mock(bug_target_name=n, status=s)
        for n, s in zip(['systemd (Ubuntu)',
                         'vim (Debian)',
                         'glibc (Ubuntu)'],
                        ['New',
                         'Confirmed',
                         'New'])
    ]

    bug2 = Mock()
    bug2.title = "This is the title of another bug"
    bug2.description = "This is the longer description"
    bug2.heat = "200"
    bug2.importance = "Undecided"
    bug2.bug_tasks = [
        Mock(bug_target_name=s)
        for s in [
            'systemd (Ubuntu)',
            'systemd (Ubuntu Focal)',
            'systemd (Ubuntu Bionic)',
            'vim (Debian)']
    ]

    bug3 = Mock()
    bug3.title = "This is the title of a third bug"
    bug3.description = "This is the longer description"
    bug3.heat = "300"
    bug3.importance = "Undecided"
    bug3.bug_tasks = [
        Mock(bug_target_name=n, status=s)
        for n, s in zip(
            ['systemd (Ubuntu)',
             'systemd (Ubuntu Focal)',
             'systemd (Ubuntu Bionic)',
             'vim (Debian)',
             'glibc (Ubuntu)',
             'glibc (Ubuntu Focal)',
             'glibc (Ubuntu None)',
             'glibc !@#$)',
             'glibc (Ubuntu Bionic)'],
            ['New',
             'New',
             'New',
             'New',
             'New',
             'Incomplete',
             'New',
             'New',
             'Confirmed']
        )
    ]

    bug4 = Mock()
    bug4.title = "This is the title of a casper bug"
    bug4.description = "This is the longer description"
    bug4.heat = "350"
    bug4.importance = "Undecided"
    bug4.bug_tasks = [
        Mock(bug_target_name=n, status=s)
        for n, s in zip(
            ['casper (Ubuntu)',
             'casper (Ubuntu '+ubuntu_devel+')'],
            ['New', 'New'])
    ]

    bug5 = Mock()
    bug5.title = "This is the title of a bug"
    bug5.heat = "100"
    bug5.bug_tasks = []

    bug6 = Mock()
    bug6.title = "This is the title of a bug"
    bug6.heat = "100"
    bug6.bug_tasks = [Mock(
            bug_target_name='systemd (Ubuntu)',
            status='New',
            importance='Critical')]

    return Mock(bugs={
            1: bug1,
            2: bug2,
            3: bug3,
            4: bug4,
            5: bug5,
            6: bug6
                })


@pytest.fixture
def empty_bug():
    bug = Mock()
    bug.title = ""
    bug.description = ""
    bug.id = 0
    bug.tags = []
    bug.web_link = "https://"
    bug.bug_tasks = []

    return bug


@pytest.fixture
def lp():
    bug = Mock()
    bug.title = "test bug"
    bug.id = 123456
    bug.bug_tasks = [
        Mock(bug_target_name=n, status=s)
        for n, s in zip(['systemd (Ubuntu)',
                         'vim (Debian)',
                         'glibc (Ubuntu)'],
                        ['New',
                         'Confirmed',
                         'New'])
    ]

    project1 = Mock()
    project1.searchTasks = Mock(return_value=None)

    project2 = Mock()
    project2.searchTasks = Mock(return_value=bug)

    return Mock(
        bugs={123456: bug},
        projects={"subiquity": project1, "curtin": project2})


@pytest.fixture
def jira():
    api = Mock()
    api.search_issues = Mock(return_value=None)

    return api


@pytest.fixture
def issue():
    return {
                'JIRA ID': "KEY-001",
                'Summary': "LP#123456 [jira] Default JIRA Bug",
                'Status': "In Progress",
                'LaunchPad ID': '123456',
                'Heat': '',
                'Importance': '',
                'Packages': '',
                "Devel": '',
                "Impish": '',
                "Hirsute": '',
                "Focal": '',
                "Bionic": '',
                "Xenial": '',
                "Trusty": ''
            }
