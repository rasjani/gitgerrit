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
from pprint import pprint

__version__ = get_versions()['version']
TRIGGER_WORD="funverify"

@log_decorator
def get_git_root() -> git.repo.base.Repo:
    """ Tries to locate a the root of the current git repository and and returns Repo instance"""
    try:
        entry = Path(os.environ.get("WORKSPACE", ".")).absolute()
        return git.Repo(entry, search_parent_directories=True)
    except Exception as error:
        raise RuntimeError(f"Creating git repo object from {entry} failed with error: {error}!")

def get_change_detail(rest, changeid):
    return rest.get(f"/changes/{changeid}/detail?o=CURRENT_REVISION")

def print_votes(changedata):
    for label in ["Code-Review", "Verified"]:
        print(f"{label}:")
        for vote in changedata['labels'][label]['all']:
            if vote["value"] != 0:
                print(f" * {vote['name']:30}{vote['value']}")

def trigger_run_verify(rest, changeid, revision):
    """Adds "runverify" comment to a given review"""
    return rest.post(f"/changes/{changeid}/revisions/{revision}/review/", return_response=True, data={"message": TRIGGER_WORD})

def runverify(rest, git_repo, args):
    response = get_change_detail(rest, args.changeid)
    if args.check:
        print_votes(response)
        # pprint(response)
    else:
        current_rev = response["current_revision"]
        revision = response["revisions"][current_rev]["_number"]
        trigger_run_verify(rest, args.changeid, revision)

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
    parser.add_argument("--commit", default=None, metavar="N", type=str)
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
    if "cmd" not in args:
        parser.print_help()
        sys.exit(0)
    return args


def get_gerrit_configuration(cfg):
    result = {}
    base_error = "Configuration Error"
    keys = ["user", "token", "host"]
    if cfg.has_section("gerrit"):
        for key in keys:
            if not cfg.has_option("gerrit", key):
                raise RuntimeError(f"{base_error}: missing option '{key}' in section gerrit in your git configuration")
            result[key] = cfg.get("gerrit", key)
    else:
        for key in keys:
            result[key] = os.environ.get(f"GERRIT_{key.upper()}", None)

        if None in result.values():
            raise RuntimeError(f"{base_error}: missing gerrit section in your git configuration and no fallback values in environment")

    return result

@log_decorator
def gerrit_api(gerrit_config, verify_ssl = True):
    """Returns GerritRestAPI instance with authentication details"""
    auth = HTTPBasicAuth(gerrit_config["user"], gerrit_config["token"])
    return GerritRestAPI(url=f"https://{gerrit_config['host']}", auth=auth, verify=verify_ssl)

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
    args.cmd(rest, git_repo, args)
