import pytest

from unittest.mock import Mock

from LpToJira.lp_to_jira import  get_lp_bug, get_lp_bug_pkg


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

    return Mock(bugs={123456: bug})


def test_get_lp_bug(lp):
    # bad bug id
    assert get_lp_bug(lp, 1000000000) == None
    # bad launchpad api
    assert get_lp_bug(None, 123456) == None
    # valid bug
    test_bug = get_lp_bug(lp, 123456)
    assert test_bug.id == 123456
    assert test_bug.title == "test bug"


def test_get_lp_bug_pkg():
    bug = Mock()
    bug.bug_tasks = [Mock(bug_target_name='systemd (Ubuntu)')]

    assert get_lp_bug_pkg(bug) == 'systemd'

    bug = Mock()
    bug.bug_tasks = [Mock(bug_target_name='systemd (Ubuntu Focal)')]

    assert get_lp_bug_pkg(bug) == 'systemd'

    bug = Mock()
    bug.bug_tasks = [Mock(bug_target_name='glibc !@#$)')]

    assert get_lp_bug_pkg(bug) == None

    bug = Mock()
    bug.bug_tasks = [Mock(bug_target_name='systemd (Debian)')]

    assert get_lp_bug_pkg(bug) == None

    bug = Mock()
    bug.bug_tasks = [
        Mock(bug_target_name=n)
        for n in ['systemd (Ubuntu)', 'glibc (Ubuntu)']]

    assert get_lp_bug_pkg(bug) == 'glibc'

# =============================================================================
