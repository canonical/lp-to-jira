import pytest

from unittest.mock import Mock

from LpToJira.lp_to_jira import\
    build_jira_issue,\
    create_jira_issue,\
    get_lp_bug,\
    get_lp_bug_pkg,\
    get_all_lp_project_bug_tasks,\
    is_bug_in_jira,\
    lp_to_jira_bug


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


def test_get_lp_project_bug_tasks(lp):
    # Very light testing of what the function could do
    # 100% coverage but not necessarly 100% coverage :)
    # TODO: test more date's options
    # TODO: test various status filters

    assert get_all_lp_project_bug_tasks(lp, "badproject") == None

    # project subiquity exists has no bug
    assert get_all_lp_project_bug_tasks(lp, "subiquity") == None

    # project curtin exists and has a bug
    assert get_all_lp_project_bug_tasks(lp, "curtin", 5).id == 123456


def test_is_bug_in_jira():
    jira = Mock()
    jira.search_issues = Mock(return_value=None)

    bug = Mock()
    bug.id = 123

    assert is_bug_in_jira(jira, bug, "AA") == False

    jira_issue = Mock()
    jira_issue = [Mock(key="key")]

    jira.search_issues = Mock(return_value=jira_issue)
    jira.client_info = Mock(return_value="jira_client_info")

    assert is_bug_in_jira(jira, bug, "AA") == True


def test_build_jira_issue(empty_bug):
    # TODO improve coverage to test for non empty bug
    default_jira_bug = {'project': '',
                        'summary': 'LP#0 [None] ',
                        'description': '', 'issuetype': {'name': 'Bug'},
                        'components': [{'name': 'Distro'}]}

    assert build_jira_issue(None, empty_bug, "") == default_jira_bug


def test_create_jira_issue(empty_bug, capsys):
    jira = Mock()

    jira.create_issue = Mock(return_value=Mock(key="001"))
    jira.add_simple_link = Mock(return_value=None)
    jira.client_info = Mock(return_value="jira")

    issue_dict = build_jira_issue(None, empty_bug, "")

    jira_issue = create_jira_issue(jira, issue_dict, empty_bug)

    assert "jira/browse/001" in capsys.readouterr().out

    # TODO: Figure out how to make this test succeed, this helps make
    #       sure the url is created properly
    # assert jira.add_simple_link.assert_called_with(
    #     jira_issue,
    #     object={'url': 'https://', 'title': 'Launchpad Link'})


def test_lp_to_jira_bug(lp, empty_bug):
    jira = Mock()

    jira_issue = [Mock(key="key")]
    jira.search_issues = Mock(return_value=jira_issue)
    jira.client_info = Mock(return_value="jira")

    lp_to_jira_bug(lp, jira, empty_bug, "AA", [''])

    jira.search_issues = Mock(return_value=None)

    opts = Mock()
    opts.label = ""
    lp_to_jira_bug(lp, jira, empty_bug, "AA", opts)

    opts.label = "label"
    lp_to_jira_bug(lp, jira, empty_bug, "AA", opts)

    opts.no_lp_tag = False
    lp_to_jira_bug(lp, jira, empty_bug, "AA", opts)


# =============================================================================