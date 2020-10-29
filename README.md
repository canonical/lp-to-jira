# lp-to-jira
Python helper script that create a new JIRA bug entry from an existing Launchpad bug id

## Launchpad
https://launchpad.net/
lp-to-jira will access launchpad as a anonymous user for now so private bug might not be visible  

## JIRA
a JIRA account is required You will need to setup a JIRA token to access your server.
On the first launch lp-to-jira will assist you in getting your jira API token.
JIRA API token can be created here https://id.atlassian.com/manage-profile/security/api-tokens

## Usage:
```
usage: lp-to-jira [options] bug-id project-id

Create JIRA entry for a given Launchpad bug ID

options:
    -e, --exists"
                Look if the Launchpad Bug has alreaady been imported
                print the JIRA issue ID if found
    -l, --label LABEL
                Add LABEL to the JIRA issue after creation

Examples:
    lp-to-jira 3215487 FR
    lp-to-jira -e 3215487 FR
    lp-to-jira -l ubuntu-meeting 3215487 PR
```
