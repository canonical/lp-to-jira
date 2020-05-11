#!/usr/bin/python3
# The purpose of lp-to-JIRA is to take a launchad bug ID and create a new Entry in JIRA


import sys
from launchpadlib.launchpad import Launchpad
from jira import JIRA


# Ex:
#     lp-to-JIRA bug_id
#     lp-to-JIRA 32165487 CI20


def usage():
    print("usage    lp-to-jira bug-id project-id")
    print("for ex:  lp-to-jira 3215487 CI20")
    print("On first launch, your JIRA server and credential will be asked and stored for future use")

# Program Flow

# 0. make sure there's 2 arguments
if len(sys.argv) != 3:
    usage()
    sys.exit(1)

bug_number = sys.argv[1]
project_id = sys.argv[2]

# 1. Connect to Launchpad API
#     anonymouse login should be enough for now
#TODO: implement with customize login/password to allow this work with private bugs

#TODO: catch exception if the Launchpad API isn't open
lp = launchpad = Launchpad.login_anonymously('anonymous', 'production', version='devel')


# 2. Make sure the bug ID exist

#TODO: catch exception if the bug can't be found
bug = lp.bugs[bug_number]

# 3. Connect to the JIRA API
#     If no token Found, explain how to get a token
#TODO: On first launch, ask user for server, login and token and store them into $HOME/.jira.token

jira_server = 'https://canonical-poc.atlassian.net/'
jira_login = 'matthieu.clemenceau@canonical.com'
jira_token = '4ctJsEyFcCddo40a20JEE222'

#TODO catch execption when it dosn't connect
jira = JIRA(jira_server,basic_auth=(jira_login,jira_token))

# 4. Make sure that there's no bug in JIRA with the same ID than the Bug you're trying to import
#TODO Find a way to differentiate imported bug with other bugs (title?)

# 5. import the bug and return the JIRA ID for said bug
new_issue = jira.create_issue(  project='CI20', 
                                summary=bug.title,
                                description=bug.description, 
                                issuetype={'name': 'Bug'})

print("Created " + new_issue.permalink)