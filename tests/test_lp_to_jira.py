import pytest

from unittest import TestCase
from unittest.mock import Mock

from LpToJira.lp_to_jira import  get_lp_bug, get_lp_bug_pkg

class test_lp(TestCase):

    def setUp(self):
        self.lp = Mock()
        self.bug = Mock()
        self.bug.title = "test bug"
        self.bug.id = 123456
        self.lp.bugs = {123456:self.bug}

        self.task1 = Mock()
        self.task2 = Mock()
        self.task3 = Mock()
        self.task4 = Mock()
        self.task5 = Mock()
        self.task6 = Mock()
        self.task7 = Mock()
        self.task8 = Mock()
        self.task9 = Mock()
        self.task10 = Mock()
        self.task11 = Mock()

        self.task1.bug_target_name = 'systemd (Ubuntu)'
        self.task2.bug_target_name = 'vim (Debian)'
        self.task3.bug_target_name = 'glibc (Ubuntu)'
        self.task4.bug_target_name = 'glibc (Ubuntu Focal)'
        self.task5.bug_target_name = 'glibc (Ubuntu None)'
        self.task6.bug_target_name = 'glibc !@#$)'
        self.task7.bug_target_name = 'systemd (Ubuntu Focal)'
        self.task8.bug_target_name = 'systemd (Ubuntu Bionic)'
        self.task9.bug_target_name = 'glibc (Ubuntu Bionic)'
        self.task10.bug_target_name = 'casper (Ubuntu)'
        self.task11.bug_target_name = 'casper (Ubuntu Impish)'

    def tearDown(self):
        pass

    def test_get_lp_bug(self):
        # bad bug id
        self.assertIsNone(get_lp_bug(self.lp, 1000000000))
        # bad launchpad api
        self.assertIsNone(get_lp_bug(None, 123456))
        # valid bug
        test_bug = get_lp_bug(self.lp, 123456)
        self.assertEqual(123456, test_bug.id)
        self.assertEqual("test bug", test_bug.title)

    def test_get_lp_bug_pkg(self):
        self.bug.bug_tasks = [self.task1]
        self.assertEqual(get_lp_bug_pkg(self.bug), 'systemd')

        self.bug.bug_tasks = [self.task1, self.task3]
        self.assertEqual(get_lp_bug_pkg(self.bug), 'glibc')

        self.bug.bug_tasks = [self.task10, self.task11]
        self.assertEqual(get_lp_bug_pkg(self.bug), 'casper')

        self.bug.bug_tasks = [self.task2]
        self.assertIsNone(get_lp_bug_pkg(self.bug))

    def test_get_all_lp_project_bug_tasks(self):
        self.assertEqual(0,1)

# =============================================================================
