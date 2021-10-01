#!/usr/bin/python3
# The purpose of lp-to-jira is to take a launchad bug ID and
# create a new Entry in JIRA in a given project


import os
import json
import datetime

import argparse
import textwrap

from launchpadlib.launchpad import Launchpad
from launchpadlib.credentials import UnencryptedFileCredentialStore

from jira import JIRA
from LpToJira.jira_api import jira_api


jira_server = ""
jira_project = ""

jira_lp_db = []

jira = None
api = None

series = ["Devel",
          "Hirsute",
          "Focal",
          "Bionic",
          "Xenial",
          "Trusty"]

colummns = ["Jira ID",
            "Summary",
            "Status",
            "LaunchPad ID",
            "Heat",
            "Importance",
            "Packages",
            ] + series

importance_color = {
    "Critical": 'style="color:#d12b1f"',
    "High": 'style="color:#e07714"',
    "Medium": 'style="color:#0b9b3d"',
    "Low": "",
    "Wishlist": 'style="color:#2727a7"',
    "Undecided": 'style="color:#6d6d6e"',
    "Unknown": ""
}

status_color = {
    "New": 'style="background-color:#af7850"',
    "Confirmed": 'style="background-color:#E94348"',
    "Incomplete": 'style="background-color:#E94348"',
    "Triaged": 'style="background-color:#F77200"',
    "Fix Committed": 'style="background-color:#b5d4a7"',
    "Fix Released": 'style="background-color:#6ab44b"'
}


def status_cell(status):
    return "<td %s>%s</td>" % (status_color.get(status, ""), status)


def java_script():
    'Sort a table https://www.w3schools.com/howto/howto_js_sort_table.asp'
    'Addition of numeric boolean to allow sorting based on numbers'
    script = """\
    <script>
    function search() {
		// Declare variables
		var input, filter, table, lines, line, value, show, i, txtValue;
		input = document.getElementById("myInput");
		filter = input.value.toUpperCase();
		table = document.getElementById("JIRA-LP-TABLE");
		lines = table.getElementsByTagName("TR");

		// Loop through all table rows, and hide those who don't match the search query
		for (i = 1; i < lines.length; i++) {
			line = lines[i].getElementsByTagName("TD");
			show = false;
			for (j = 0; j < line.length; j++) {
				value = line[j];
				if (value) {
					txtValue = value.textContent || value.innerText;
					if (txtValue.toUpperCase().indexOf(filter) > -1) {
						show = true;
						break;
					}
				}
			}
			if(show)
				lines[i].style.display = "";
			else
				lines[i].style.display = "none";
		}
	}

    function sortTable(n,numerical) {
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount=0;
        table = document.getElementById("JIRA-LP-TABLE");
        switching = true;
        // Set the sorting direction to ascending:
        dir = "asc";
        /* Make a loop that will continue until
        no switching has been done: */
        while (switching) {
        // Start by saying: no switching is done:
        switching = false;
        rows = table.rows;
        /* Loop through all table rows (except the
        first, which contains table headers): */
        for (i = 1; i < (rows.length - 1); i++) {
            // Start by saying there should be no switching:
            shouldSwitch = false;
            /* Get the two elements you want to compare,
            one from current row and one from the next: */
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            /* Check if the two rows should switch place,
            based on the direction, asc or desc: */
            if (dir == "asc") {
            if (numerical) {
                //check if the two rows should switch place:
                if (Number(x.innerHTML) < Number(y.innerHTML)) {
                    //if so, mark as a switch and break the loop:
                    shouldSwitch = true;
                    break;
                }
            }
            else if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                // If so, mark as a switch and break the loop:
                shouldSwitch = true;
                break;
            }
            } else if (dir == "desc") {
            if (numerical) {
                //check if the two rows should switch place:
                if (Number(x.innerHTML) > Number(y.innerHTML)) {
                    //if so, mark as a switch and break the loop:
                    shouldSwitch = true;
                    break;
                }
            }
            else if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                // If so, mark as a switch and break the loop:
                shouldSwitch = true;
                break;
            }
            }
        }
        if (shouldSwitch) {
            /* If a switch has been marked, make the switch
            and mark that a switch has been done: */
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            // Each time a switch is done, increase this count by 1:
            switchcount ++;
        } else {
            /* If no switching has been done AND the direction is "asc",
            set the direction to "desc" and run the while loop again. */
            if (switchcount == 0 && dir == "asc") {
            dir = "desc";
            switching = true;
            }
        }
        }
    }
    </script>
    """

    return script


def print_html_report(file):
    html_data = """\
    <!DOCTYPE html>
    <html><title>Foundations JIRA / Launchpad status</title>
    <head>
    <style>
		#myInput {
		background-position: 10px 12px; /* Position the search icon */
		background-repeat: no-repeat; /* Do not repeat the icon image */
		width: 100%; /* Full-width */
		font-size: 14px; /* Increase font-size */
		padding: 12px 20px 12px 40px; /* Add some padding */
		border: 1px solid #ddd; /* Add a grey border */
		margin-bottom: 12px; /* Add some space below the input */
		}

		#JIRA-LP-TABLE th, #JIRA-LP-TABLE td {
		text-align: left; /* Left-align text */
		}

		#JIRA-LP-TABLE tr {
		/* Add a bottom border to all table rows */
		border-bottom: 1px solid #ddd;
		}

		#JIRA-LP-TABLE tr.header, #JIRA-LP-TABLE tr:hover {
		/* Add a grey background color to the table header and on hover */
		background-color: #f1f1f1;
		}

		table, th, td {
        border: 1px solid black;
		}

    </style>
    </head>
    """
    html_data += java_script()

    html_data += "<body>\n"

    html_data += "<p>Report generated on {}</p>\n" \
        .format(datetime.datetime.now())
    html_data += '<input type="text" id="myInput" onkeyup="search()" placeholder="Search ..">'
    html_data += '<table id="JIRA-LP-TABLE">\n'

    title = True
    for entry in jira_lp_db:
        if title:
            headers = entry.keys()
            line = ""
            line += "<tr>\n"
            index = 0
            for header in headers:
                line += '<th onclick="sortTable(%d,false)">%s</th>\n' % \
                    (index, header)
                index += 1
            line += "</tr>\n"
            html_data += line
            title = False

        line = "<tr>\n"
        line += "\t<td><a href=%s/browse/%s>%s</a></td>\n" % \
            (jira_server, entry['JIRA ID'], entry['JIRA ID'])
        line += "\t<td>%s</td>\n" % \
            (entry['Summary'][:80]+" ..." if len(entry['Summary']) > 80
                else entry['Summary'])
        line += "\t<td>%s</td>\n" % entry['Status']

        line += "\t<td><a href=https://pad.lv/%s>LP#%s</a></td>\n" % \
            (entry['LaunchPad ID'], entry['LaunchPad ID'])
        line += "\t<td>%s</td>\n" % entry['Heat']
        line += "\t<td %s><b>%s</b></td>\n" % \
            (importance_color.get(entry['Importance']), entry['Importance'])
        line += "\t<td>%s</td>\n" % \
            ("multiple packages" if len(entry['Packages'].split(",")) > 2
                else entry['Packages'])

        for serie in series:
            line += ("\t" + status_cell(entry[serie]) + "\n")

        line += "</tr>\n"
        html_data += line + "\n"

    html_data += "</table>"
    html_data += "</body></html>"

    with open(file, 'w') as html_file:
        html_file.write(html_data)


def print_table(
        table,
        sep="|",
        draw_title=True,
        limit=60,
        align=True,
        file="/dev/stdout"):
    """
    Print a 2D list on stdout assuming it is rectangular (matrix) shape (NxM)
    TODO: handle non rectangular list
    limit: allows to limit the maximum size per column (default 60)
    draw_title: if the first line of your table is the header
        this will print a line underneath
    """

    if not table:
        return

    # How many Columns
    cols = len(table[0])

    # Assume every line of the table are identical
    cols_size = [len(max([id[i] for id in table], key=len))
                 for i in range(cols)]

    # limit size of some cloumns if needed
    cols_size = [limit if x > limit else x for x in cols_size]

    with open(file, 'w') as output_file:
        for line in table:
            if align:
                line_adjust = ['{:{width}s}'.format(
                    line[x][:limit], width=cols_size[x]) for x in range(cols)]
            else:
                line_adjust = line

            output_file.write(sep.join(line_adjust)+"\n")

            # First line ?
            if draw_title:
                output_file.write("-" * len(sep.join(line_adjust))+"\n")
                draw_title = False


def get_bug_id(summary):
    "Extract the bug id from a jira title whivh would icnlude LP#"
    id = ""

    if "LP#" in summary:
        for char in summary[summary.find("LP#")+3:]:
            if char.isdigit():
                id = id + char
            else:
                break

    return id


def main(args=None):
    global jira_server

    opt_parser = argparse.ArgumentParser(
            description="Report the status of all active LaunchPad bug "\
                "imported into a JIRA project with lp-to-jira",
            formatter_class=argparse.RawTextHelpFormatter,
            epilog=textwrap.dedent('''\
            Examples:
                lp-to-jira-report FR
                lp-to-jira-report --csv  results.csv  FR
                lp-to-jira-report --json results.json FR
                lp-to-jira-report --html results.html FR
            ''')
        )
    opt_parser.add_argument(
        'project', type=str,
        help="The JIRA project string key")

    opt_parser.add_argument(
        '--csv',
        dest='csv',
        help='export the results of the report into FILE in csv format',
    )
    opt_parser.add_argument(
        '--html',
        dest='html',
        help='export the results of the report into FILE in html format',
    )
    opt_parser.add_argument(
        '--json',
        dest='json',
        help='export the results of the report into FILE in json format',
    )
    opts = opt_parser.parse_args(args)

    jira_project = opts.project

    # 1. Initialize JIRA API
    print("Initialize JIRA API ...")
    api = jira_api()
    jira_server = api.server
    jira = JIRA(api.server, basic_auth=(api.login, api.token))

    # TODO: catch exception if the Launchpad API isn't open
    # 2. Initialize Launchpad API
    # Connect to Launchpad API
    # TODO: catch exception if the Launchpad API isn't open
    snap_home = os.getenv("SNAP_USER_COMMON")
    if snap_home:
        credential_store = UnencryptedFileCredentialStore("{}/.lp_creds".format(snap_home))
    else:
        credential_store = UnencryptedFileCredentialStore(os.path.expanduser("~/.lp_creds"))
    lp = Launchpad.login_with(
        'foundations',
        'production',
        version='devel',credential_store=credential_store)

    # 3. Create Joint Structure
    # 3.a search for all JIRA issues that starts with LP#
    print("Searching for JIRA issues ...", flush=True)
    # Get JIRA issues in batch of 50
    num_issues = 0
    issue_index = 0
    issue_batch = 50

    while True:
        start_index = issue_index * issue_batch
        request = "project = {} " \
            "AND summary ~ \"LP#\" " \
            "AND status in (BLOCKED, Backlog, \"In Progress\", " \
            "REVIEW,\"Selected for Development\")""".format(jira_project)
        issues = jira.search_issues(request, startAt=start_index)

        if not issues:
            break

        issue_index += 1
        # For each issue in JIRA with LP# in the title
        for issue in issues:
            summary = issue.fields.summary
            if "LP#" in summary:
                num_issues += 1
                print("#", flush=True, end="")

                lpbug_id = get_bug_id(summary)
                lpbug_importance = ""
                lpbug_devel = ""
                lpbug_hirsute = ""
                lpbug_focal = ""
                lpbug_bionic = ""
                lpbug_xenial = ""
                lpbug_trusty = ""

                try:
                    lpbug = lp.bugs[int(lpbug_id)]

                    list_pkg = [x.bug_target_name.split()[0]
                                for x in lpbug.bug_tasks
                                if "(Ubuntu)" in x.bug_target_name]
                    bug_pkg = ", ".join(list_pkg)
                    if len(list_pkg) == 1:
                        lpbug_importance = list(importance_color.keys())[min([list(importance_color.keys()).index(x.importance) for x in lpbug.bug_tasks])]
                        lpbug_devel = "".join([x.status for x in lpbug.bug_tasks if "(Ubuntu)" in x.bug_target_name])
                        lpbug_hirsute = "".join([x.status for x in lpbug.bug_tasks if "(Ubuntu Hirsute)" in x.bug_target_name])
                        lpbug_focal = "".join([x.status for x in lpbug.bug_tasks if "(Ubuntu Focal)" in x.bug_target_name])
                        lpbug_bionic = "".join([x.status for x in lpbug.bug_tasks if "(Ubuntu Bionic)" in x.bug_target_name])
                        lpbug_xenial = "".join([x.status for x in lpbug.bug_tasks if "(Ubuntu Xenial)" in x.bug_target_name])
                        lpbug_trusty = "".join([x.status for x in lpbug.bug_tasks if "(Ubuntu Trusty)" in x.bug_target_name])

                    jira_lp_db.append({
                        'JIRA ID': issue.key,
                        'Summary': summary,
                        'Status': issue.fields.status.name,
                        'LaunchPad ID': lpbug_id,
                        'Heat': str(lpbug.heat),
                        'Importance': lpbug_importance,
                        'Packages': bug_pkg,
                        "Devel": lpbug_devel,
                        "Hirsute": lpbug_hirsute,
                        "Focal": lpbug_focal,
                        "Bionic": lpbug_bionic,
                        "Xenial": lpbug_xenial,
                        "Trusty": lpbug_trusty
                    })

                except Exception:
                    print("\nCouldn't find the Launchpad bug {}".format(lpbug_id))
                    jira_lp_db.append({
                        'JIRA ID': issue.key,
                        'Summary': summary,
                        'Status': issue.fields.status.name,
                        'LaunchPad ID': "N/A",
                        'Heat': "N/A",
                        'Importance': "N/A",
                        'Packages': "N/A",
                        "Devel": "N/A",
                        "Hirsute": "N/A",
                        "Focal": "N/A",
                        "Bionic": "N/A",
                        "Xenial": "N/A",
                        "Trusty": "N/A"
                    })

    print("\nFound %s issues" % len(jira_lp_db))

    # Create a table version of the
    jira_lp_db_table = []
    if jira_lp_db:
        jira_lp_db_table.append(list(jira_lp_db[0].keys()))
        jira_lp_db_table += [list(x.values()) for x in jira_lp_db]
    else:
        return 1

    # Display the content of jira_lp_db based on the output option
    if opts.json:
        with open(opts.json, 'w') as fp:
            json.dump(jira_lp_db, fp, indent=2)
        print("JSON report saved as %s" % opts.json)

    if opts.html:
        print_html_report(opts.html)
        print("HTML report saved as %s" % opts.html)

    if opts.csv:
        print_table(jira_lp_db_table, sep=";", limit=1024,
                    align=False, draw_title=False, file=opts.csv)
        print("CSV report saved as %s" % opts.csv)

    if not opts.csv and not opts.html and not opts.json:
        print_table(jira_lp_db_table, sep=" | ", limit=60,
                    align=True, draw_title=True, file="/dev/stdout")

    return 0
