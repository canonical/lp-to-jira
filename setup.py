import setuptools

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="LpToJira",
    version="0.6",
    author="Matthieu Clemenceau",
    author_email="matthieu.clemenceau@canonical.com",
    description=("A Command Line helper to import launchpad bug in JIRA."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/canonical/lp-to-jira",
    project_urls={
        'Bug Reports': 'https://github.com/canonical/lp-to-jira/issues',
        'Source': 'https://github.com/canonical/lp-to-jira',
    },
    packages=setuptools.find_packages(),
    keywords='lp to jira',
    entry_points={
        'console_scripts': [
            'lp-to-jira=LpToJira.lp_to_jira:main',
            'lp-to-jira-report=LpToJira.lp_to_jira_report:main',
        ],
    },
    install_requires=['jira','launchpadlib'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
