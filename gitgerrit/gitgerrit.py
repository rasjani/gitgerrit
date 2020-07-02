from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import run, CalledProcessError, CompletedProcess
from datetime import datetime
import os
import re
import logging
import argparse
import sys
import git
from pygerrit2 import GerritRestAPI, HTTPBasicAuth
from .logger import LOGGER, _APPNAME, LOG_LEVELS, log_decorator
from ._version import get_versions
__version__ = get_versions()['version']

from pprint import pprint
@log_decorator
def get_git_root() -> git.repo.base.Repo:
    """ Tries to locate a the root of the current git repository and and returns Repo instance"""
    try:
        entry = Path(os.environ.get("WORKSPACE", ".")).absolute()
        return git.Repo(entry, search_parent_directories=True)
    except Exception as error:
        raise RuntimeError(f"Creating git repo object from {entry} failed with error: {error}!")

def runverify(gerit_api, git_repo, args):
    if args.check:
        print("GET RUNVERIFY STATUS", args.changeid)
    else:
        print("TRIGGER RUNVERIFY", args.changeid)

def abandon(gerit_api, git_repo, args):
    print("ABANDON")

def topic(gerit_api, git_repo, args):
    print("TOPIC")

def parse_args():
    parser = argparse.ArgumentParser(
        prog=_APPNAME, description="yey", formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l", "--loglevel", default="info", dest="loglevel", choices=list(LOG_LEVELS.keys())[1:], help="Log Level"
    )
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s {version}".format(version=__version__)
    )

    parser.add_argument("--changeid", default=None, metavar="N", type=str)
    sub_parsers = parser.add_subparsers(help="sub-commands help")

    runverify_parser = sub_parsers.add_parser("runverify", help="runverify help")
    runverify_parser.add_argument("-c","--check", action="store_true", default=False, help="check current status")
    runverify_parser.set_defaults(cmd=runverify)

    topic_parser = sub_parsers.add_parser("topic", help="topic help")
    topic_parser.set_defaults(cmd=topic)

    abandon_parser = sub_parsers.add_parser("abandon", help="abandon help")
    abandon_parser.set_defaults(cmd=abandon)

    args = parser.parse_args(sys.argv[1:])
    LOGGER.setLevel(LOG_LEVELS[args.loglevel])
    return args


def get_gerrit_configuration(cfg):
    result = {}
    base_error = "Configuration Error"
    if  not cfg.has_section("gerrit"):
        raise RuntimeError(f"{base_error}: missing gerrit section in your git configuration")
    for key in ["user", "token", "host"]:
        if not cfg.has_option("gerrit", key):
            raise RuntimeError(f"{base_error}: missing option '{key}' in section gerrit in your git configuration")
        result[key] = cfg.get("gerrit", key)

    return result

@log_decorator
def gerrit_api(gerrit_config, verify_ssl = True):
    """Returns GerritRestAPI instance with authentication details"""
    auth = HTTPBasicAuth(gerrit_config["user"], gerrit_config["token"])
    return GerritRestAPI(url=gerrit_config["host"], auth=auth, verify=verify_ssl)

@log_decorator
def main():
    args = parse_args()
    LOGGER.debug("Hello World")
    git_repo = get_git_root()

    git_config = git_repo.config_reader()
    try:
        gerrit_config = get_gerrit_configuration(git_config)
    except RuntimeError as e:
        LOGGER.error(str(e))
        sys.exit(1)

    rest = gerrit_api(gerrit_config)
    args.cmd(gerrit_api, git_repo, args)
