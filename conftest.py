import pytest

from unittest.mock import Mock


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
