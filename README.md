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
usage: lp-to-jira [-h] [-l LABEL] [-c COMPONENT] [-E EPIC] [-e] [-s SYNC_PROJECT_BUGS] [-d DAYS] [--no-lp-tag] [bug] project

A script create JIRA issue from Launchpad bugs

positional arguments:
  bug                   The Launchpad numeric bug ID
  project               The JIRA project string key

optional arguments:
  -h, --help            show this help message and exit
  -l LABEL, --label LABEL
                        Add LABEL to the JIRA issue after creation
  -c COMPONENT, --component COMPONENT
                        Specify COMPONENT to assign the issue to
  -E EPIC, --epic EPIC  Specify EPIC to link this new issue to
  -e, --exists
                        Look if the Launchpad Bug has already been imported
                        print the JIRA issue ID if found
  -s SYNC_PROJECT_BUGS, --sync_project_bugs SYNC_PROJECT_BUGS
                        Adds all bugs from a specified LP Project to specified Jira board
                        if they are not already on the Jira board.
                        Use --days to narrow down bugs
  -d DAYS, --days DAYS  Only look for LP Bugs in the past n days
  --no-lp-tag           Do not add tag to LP Bug

Examples:
    lp-to-jira 3215487 FR
    lp-to-jira -e 3215487 FR
    lp-to-jira -l ubuntu-meeting 3215487 PR
    lp-to-jira -s ubuntu -d 3 IQA
    lp-to-jira --no-lp-tag -c Network -E FS-543 123231 PR
```

# lp-to-jira-report
Python helper script that produce reports listing all the bugs in a given project that have been imported with lp-to-jira
(issues that have LP#1234567 in their titles)
This report will show JIRA status for the issues and LP status for the related LP bugs in all impacted series.

## Usage:
```
usage: lp-to-jira-report [options] project-id

Report the status of all active LaunchPad bug imported
into a JIRA project with lp-to-jira

options:
    --csv FILE
        export the results of the report into FILE in csv format
    --html FILE
        export the results of the report into FILE in html format
    --json FILE
        export the results of the report into FILE in json format
    default:
        display the report on stdout

Examples:
    lp-to-jira-report FR
    lp-to-jira-report --csv  results.csv  FR
    lp-to-jira-report --json results.json FR
    lp-to-jira-report --html results.html FR
```

## Sync while getting a report
```
usage: lp-to-jira-report [options] --sync project-id
```

This will perform the same as lp-to-jira-report except that will also sync
some fata from Launchpad back into your JIRA issues

- Title Sync: If the Launchpad Item title changed, the JIRA issues summary will be updated
- Rekease Status: If all the series impacted in Launchpad are Fix Release, the JIRA issue will automatically be moved to DONE
- It is possible to disable automation on the JIRA issue by creating a Label called DisableLPSync
