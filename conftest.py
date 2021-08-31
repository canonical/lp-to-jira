import pytest

from unittest.mock import Mock

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

    return Mock(bugs={123456: bug}, projects={"subiquity": project1, "curtin": project2})
