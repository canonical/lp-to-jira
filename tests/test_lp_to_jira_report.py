from unittest.mock import Mock


from LpToJira.lp_to_jira_report import \
    find_issues_in_project,\
    get_bug_id,\
    sync_title


def test_get_bug_id():
    assert get_bug_id("") == ""
    assert get_bug_id("LP#32165987") == "32165987"
    assert get_bug_id("LP#32165987 This is a bug") == "32165987"
    assert get_bug_id("  LP#32165987 This is a bug") == "32165987"
    assert get_bug_id("LP#32165987This is a bug") == "32165987"
    assert get_bug_id("LP#32165987 [test] This is a bug") == "32165987"
    assert get_bug_id("[SRU] LP#32165987 [test This is a bug") == "32165987"

    assert get_bug_id("LP #32165987 [test] This is a bug") == ""


def test_find_issues_in_project(issue):
    assert find_issues_in_project(None, "FR") == []

    api = Mock()
    jira_issue1 = Mock()
    jira_issue1.fields = Mock()
    jira_issue1.fields.summary = "LP#123456 [jira] Default JIRA Bug"
    jira_issue1.key = "KEY-001"
    jira_issue1.fields.status = Mock()
    jira_issue1.fields.status.name = "In Progress"

    jira_issue2 = Mock()
    jira_issue2.fields = Mock()
    jira_issue2.fields.summary = "Random bug not imported"

    api.search_issues = Mock()
    api.search_issues.side_effect = [[jira_issue1, jira_issue2], None]

    assert find_issues_in_project(api, "FOO") == [issue]


def test_sync_title(issue, jira, lp):
    assert not sync_title(None, None, None)

    # This should do a successful title change as issue
    # has different title than the corresponding bug in LP
    assert sync_title(issue, jira, lp)
    assert issue['Summary'] == "LP#123456 [jira] test bug"

    bad_issue = {
                'JIRA ID': "KEY-002",
                'Summary': "LP123456 jira Bug",
                'Status': "In Progress",
                'LaunchPad ID': '123456'
            }

    assert not sync_title(bad_issue, jira, lp)
