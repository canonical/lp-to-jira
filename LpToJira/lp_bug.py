#!/usr/bin/python3
# Simple LaunchPad Bug object used to store some informations from LaunchPad
# into a structure that can be stored in and out of a json file

ubuntu_devel = 'Jammy'

ubuntu_version = {
    ubuntu_devel: '22.04',
    'Impish': '21.10',
    'Hirsute': '21.04',
    'Groovy': '20.10',
    'Focal': '20.04',
    'Bionic': '18.04',
    'Xenial': '16.04',
    'Trusty': '14.04',
    'Precise': '12.04'
}


class lp_bug():
    def __init__(self, id, lp_api):
        self.id = int(id)

        if not lp_api:
            raise ValueError("Error with Launchpad API")

        try:
            bug = lp_api.bugs[self.id]

        except KeyError:
            raise KeyError("Bug {} isn't in Launchpad".format(id))

        self.title = bug.title
        self.description = bug.description
        self.heat = bug.heat

        self.packages_info = {}
        for task in bug.bug_tasks:
            package_name = ""

            task_name = task.bug_target_name
            if " (Ubuntu" in task_name:
                package_name = task_name.split()[0]

                if package_name not in self.packages_info.keys():
                    self.packages_info[package_name] = {}

                # Grab the Ubuntu serie our of the task name
                # Set the serie to ubuntu_devel is empty
                serie = task_name[task_name.index("Ubuntu")+7:-1]
                if serie == '':
                    serie = ubuntu_devel
                elif serie not in ubuntu_version.keys():
                    continue

                if "series" not in self.packages_info[package_name].keys():
                    self.packages_info[package_name]["series"] = {}

                if serie not in self.packages_info[package_name]["series"].keys():
                    self.packages_info[package_name]["series"][serie] = {}

                # For each impacted package/serie, capture status
                self.packages_info[package_name]["series"][serie]["status"]\
                    = task.status

                # For each impacted package/serie, capture importance
                self.packages_info[package_name]["series"][serie]["importance"]\
                    = task.importance

    @property
    def affected_packages(self):
        """
        return list of packages affected by this bug in a form of string list
        ['pkg1', 'pkg2' , 'pkg3']
        """
        return list(self.packages_info.keys())

    def affected_series(self, package):
        """
        Returns a list of string containing the series affected by a specific
        bug for a specific package: ['Impish', 'Focal', 'Bionic']
        """
        if package in self.packages_info.keys():
            return list(self.packages_info[package]['series'].keys())
        return []

    def affected_versions(self, package):
        """
        Simply return all the affected version for a specific package affected
        by this bug. Convert affected serie into a version number
        """
        return [ubuntu_version.get(x) for x in self.affected_series(package)]

    def package_detail(self, package, serie, detail):
        try:
            return self.packages_info[package]["series"][serie][detail]
        except KeyError:
            return ""

    def __repr__(self):
        return self.dict().__str__()

    def __str__(self):
        string = "LP: #{} : {}".format(self.id, self.title)
        string += "\nHeat: {}".format(self.heat)
        for pkg in self.affected_packages:
            string += "\n - {}:".format(pkg)
            for serie in self.affected_series(pkg):
                string += "\n   - {} : {} ({})".\
                    format(
                        serie,
                        self.package_detail(pkg, serie, "status"),
                        self.package_detail(pkg, serie, "importance")
                        )

        return string

    def dict(self):
        dict = {}
        dict['id'] = self.id
        dict['title'] = self.title
        dict['packages'] = self.packages_info

        return dict

# =============================================================================
