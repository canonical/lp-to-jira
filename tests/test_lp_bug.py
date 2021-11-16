import pytest

from LpToJira.lp_bug import lp_bug, ubuntu_devel, ubuntu_version


def test_bug_init_bad_lp_api():
    with pytest.raises(ValueError):
        return lp_bug(1234567, None)


def test_bug_init_bad_type_bug(lp_api):
    with pytest.raises(ValueError):
        return lp_bug("bad", lp_api)


def test_bug_init_bad_bug_doesnt_exist(lp_api):
    with pytest.raises(KeyError):
        return lp_bug(123456789, lp_api)


def test_default_init(lp_api):
    bug = lp_bug(1, lp_api)
    assert bug.id == 1
    assert bug.title == "This is the title of a bug"
    assert bug.description == "This is the longer description"
    assert bug.heat == "100"


def test_affected_packages(lp_api):
    bug1 = lp_bug(1, lp_api)
    assert bug1.affected_packages == ['systemd', 'glibc']

    bug2 = lp_bug(2, lp_api)
    assert bug2.affected_packages == ['systemd']


def test_affected_series(lp_api):

    bug = lp_bug(3, lp_api)

    # Simple default serie test
    series = bug.affected_series('systemd')

    assert series == [ubuntu_devel, 'Focal', 'Bionic']

    # Wrong Serie vim (Debian)
    series = bug.affected_series('vim')
    assert series == []

    # Ignore Bad serie glibc !@#$)
    series = bug.affected_series('glibc')
    assert series == [ubuntu_devel, 'Focal', 'Bionic']


def test_affected_series_double(lp_api):
    bug = lp_bug(4, lp_api)

    series = bug.affected_series('casper')
    assert series == [ubuntu_devel]


def test_affected_versions(lp_api):
    bug = lp_bug(3, lp_api)

    versions = bug.affected_versions('systemd')
    assert versions == [ubuntu_version[ubuntu_devel], '20.04', '18.04']

    versions = bug.affected_versions('vim')
    assert versions == []

    versions = bug.affected_versions('glibc')
    assert versions == [ubuntu_version[ubuntu_devel], '20.04', '18.04']


def test_package_detail(lp_api):
    bug = lp_bug(3, lp_api)

    # test with a missing serie and make sure it defaults to ubuntu_devel
    assert bug.package_detail("glibc", 'Focal', "status") == "Incomplete"

    assert bug.package_detail("systemd", ubuntu_devel, "status") == "New"

    # test for detail that doesn't exist
    assert bug.package_detail("systemd", ubuntu_devel, "age") == ""


def test_bug_str(lp_api):
    bug = lp_bug(5, lp_api)
    bug_str = "LP: #5 : This is the title of a bug\nHeat: 100"
    assert str(bug) == bug_str

    bug = lp_bug(6, lp_api)
    bug_str = "LP: #6 : This is the title of a bug\n"\
        "Heat: 100\n - systemd:\n   - " + ubuntu_devel + " : New (Critical)"
    assert str(bug) == bug_str


def test_bug_dict(lp_api):
    bug = lp_bug(5, lp_api)
    bug_dict = {'id': 5,
                'title': 'This is the title of a bug',
                'packages': {}}

    assert bug.dict() == bug_dict


def test_bug_repr(lp_api):
    bug = lp_bug(5, lp_api)
    bug_dict = {'id': 5,
                'title': 'This is the title of a bug',
                'packages': {}}

    assert bug.__repr__() == bug_dict.__str__()

# =============================================================================
