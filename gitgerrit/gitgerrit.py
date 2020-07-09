from pathlib import Path
import os
import re
import argparse
import sys
import git
import requests
from pygerrit2 import GerritRestAPI, HTTPBasicAuth
from .logger import LOGGER, _APPNAME, LOG_LEVELS, log_decorator
from ._version import get_versions

__version__ = get_versions()["version"]
TRIGGER_WORD = "runverify"
RE_CHANGEID = re.compile(r"change-id:\s+(?P<changeid>I[a-z0-9]+)", re.IGNORECASE | re.MULTILINE)


@log_decorator
def get_git_root() -> git.repo.base.Repo:
    """ Tries to locate a the root of the current git repository and and returns Repo instance"""
    try:
        entry = Path(os.environ.get("WORKSPACE", ".")).absolute()
        return git.Repo(entry, search_parent_directories=True)
    except Exception as error:
        raise RuntimeError(f"Creating git repo object from {entry} failed with error: {error}!")


@log_decorator
def get_change_detail(rest, changeid):
    try:
        return rest.get(f"/changes/{changeid}/detail?o=CURRENT_REVISION&o=CURRENT_COMMIT&o=WEB_LINKS")
    except requests.exceptions.HTTPError as e:
        LOGGER.debug(f"HTTP Error Occured: {str(e)}")
        raise RuntimeError(f"Provided change ({changeid}) cannot be found on remote gerrit server.")


@log_decorator
def print_votes(changedata):
    for label in ["Code-Review", "Verified"]:
        LOGGER.info(f"{label}:")
        try:
            for vote in changedata["labels"][label]["all"]:
                LOGGER.info(f" * {vote['name']:30}{vote['value']}")
        except KeyError:
            pass


@log_decorator
def trigger_run_verify(rest, changeid, revision):
    """Adds "runverify" comment to a given review"""
    return rest.post(f"/changes/{changeid}/revisions/{revision}/review/", return_response=True, data={"message": TRIGGER_WORD})


@log_decorator
def runverify(rest, git_repo, args, gerrit_config):
    response = get_change_detail(rest, args.changeid)
    if args.check:
        LOGGER.info(f"https://{gerrit_config['host']}/c/{response['project']}/+/{response['_number']}")
        print_votes(response)
    else:
        current_rev = response["current_revision"]
        revision = response["revisions"][current_rev]["_number"]
        trigger_run_verify(rest, args.changeid, revision)


@log_decorator
def abandon(gerrit_api, git_repo, args, gerrit_config):
    chain = args.commit_chain or [args.changeid]
    output_buffer = "Abandoning following changes:\n * {changes}\n".format(changes="\n * ".join(chain))
    LOGGER.info(output_buffer)
    for change in chain:
        abandon_change(gerrit_api, change)

@log_decorator
def change_topic(gerrit_api, changeid, topic):
    try:
        return gerrit_api.put(f"/changes/{changeid}/topic", data={"topic": topic})
    except requests.exceptions.HTTPError as e:
        LOGGER.debug(f"HTTP Error Occured: {str(e)}")
        raise RuntimeError(f"Provided change ({changeid}) cannot be found on remote gerrit server.")
    return gerrit_api.put(f"/changes/{changeid}/topic", data={"topic": topic})

@log_decorator
def topic(gerrit_api, git_repo, args, gerrit_config):
    chain = args.commit_chain or [args.changeid]

    if args.check:
        LOGGER.info("List of topics:")
        for change in chain:
            change_details = get_change_detail(gerrit_api, change)
            LOGGER.info(f" * {change} - {change_details['topic']}")
    else:
        if len(chain)>1:
            LOGGER.info(f"Changing topic of the commit chain parents to {topic}")
            for change in chain[1:]:
                change_topic(gerrit_api,  change, args.topic)
        else:
            LOGGER.info(f"Changing topic the commit to {topic}")
            change_topic(gerrit_api,  chain[0], args.topic)


def parse_args():
    parser = argparse.ArgumentParser(prog=_APPNAME, description="yey", formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument(
        "-l", "--loglevel", default="info", dest="loglevel", choices=list(LOG_LEVELS.keys())[1:], help="Log Level"
    )
    parser.add_argument("-v", "--version", action="version", version="%(prog)s {version}".format(version=__version__))

    parser.add_argument("--support-chain", action="store_true", default=False, help="Always operate on top of the commit chain")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--changeid", default=None, metavar="N", type=str)
    group.add_argument("--commit", default=None, metavar="N", type=str)
    sub_parsers = parser.add_subparsers(help="sub-commands help")

    runverify_parser = sub_parsers.add_parser("runverify", help="runverify help")
    runverify_parser.add_argument("-c", "--check", action="store_true", default=False, help="check current status")
    runverify_parser.set_defaults(cmd=runverify)

    topic_parser = sub_parsers.add_parser("topic", help="topic help")
    topic_parser.add_argument("-c", "--check", action="store_true", default=False, help="print current topic(s)")
    topic_parser.add_argument("-s", "--set", dest="topic", default="NOCI", help="Topic to set, defaults to NOCI")
    topic_parser.set_defaults(cmd=topic)

    abandon_parser = sub_parsers.add_parser("abandon", help="abandon help")
    abandon_parser.set_defaults(cmd=abandon)

    args = parser.parse_args(sys.argv[1:])
    LOGGER.setLevel(LOG_LEVELS[args.loglevel])
    if "cmd" not in args:
        parser.print_help()
        sys.exit(0)
    return args


@log_decorator
def get_gerrit_configuration(cfg):
    result = {}
    base_error = "Configuration Error"
    keys = ["user", "token", "host"]
    if cfg.has_section("gerrit"):
        LOGGER.debug("Found gerrit section in git config, using it for configuring git-gerrit")
        for key in keys:
            if not cfg.has_option("gerrit", key):
                raise RuntimeError(f"{base_error}: missing option '{key}' in section gerrit in your git configuration")
            result[key] = cfg.get("gerrit", key)
    else:
        LOGGER.debug("No gerrit section in git config, using environment variables as fallback configuration")
        for key in keys:
            result[key] = os.environ.get(f"GERRIT_{key.upper()}", None)

        if None in result.values():
            raise RuntimeError(
                f"{base_error}: missing gerrit section in your git configuration and no fallback values in environment"
            )

    return result


@log_decorator
def get_gerrit_api(gerrit_config, verify_ssl=True):
    """Returns GerritRestAPI instance with authentication details"""
    auth = HTTPBasicAuth(gerrit_config["user"], gerrit_config["token"])
    rest = GerritRestAPI(url=f"https://{gerrit_config['host']}", auth=auth, verify=verify_ssl)
    log_cfg = gerrit_config.copy()
    log_cfg["token"] = "<HIDDEN>"
    LOGGER.debug(f"Config: {log_cfg}")
    LOGGER.debug(f"Url: {rest.url}")
    return rest


@log_decorator
def get_changeid_of_commit(git_repo, commit):
    commit = git_repo.commit(commit)
    search_result = RE_CHANGEID.search(commit.message)
    if search_result:
        return search_result.group("changeid")
    return None

@log_decorator
def abandon_change(rest, changeid):
    try:
        return rest.post(f"/changes/{changeid}/abandon")
    except requests.exceptions.HTTPError as e:
        LOGGER.debug(f"HTTP Error Occured: {str(e)}")
        raise RuntimeError(f"Provided change ({changeid}) cannot be found on remote gerrit server.")

@log_decorator
def get_changes_submitted_together(rest, changeid):
    try:
        return rest.get(f"/changes/{changeid}/revisions/current/related")
    except requests.exceptions.HTTPError as e:
        LOGGER.debug(f"HTTP Error Occured: {str(e)}")
        raise RuntimeError(f"Provided change ({changeid}) cannot be found on remote gerrit server.")


@log_decorator
def main():
    args = parse_args()
    git_repo = get_git_root()
    git_config = git_repo.config_reader()
    try:
        gerrit_config = get_gerrit_configuration(git_config)
    except RuntimeError as e:
        LOGGER.error(str(e))
        sys.exit(1)
    rest = get_gerrit_api(gerrit_config)
    args.commit_chain = None
    if args.commit:
        LOGGER.debug("commit specified, reading changeid")
        args.changeid = get_changeid_of_commit(git_repo, args.commit)

    if not args.changeid:
        LOGGER.debug("change id is not set, reading changing from HEAD")
        args.changeid = get_changeid_of_commit(git_repo, git_repo.head.commit.hexsha)

    if args.support_chain:
        response = get_changes_submitted_together(rest, args.changeid)
        if response["changes"]:
            args.commit_chain = list(map(lambda change: change["change_id"], response["changes"]))
            LOGGER.debug(
                f"Due to commit chains support, changeid ({args.changeid}) is switched to top of the commit chain ({args.commit_chain[0]})"
            )
            LOGGER.debug(args.commit_chain)
            args.changeid = args.commit_chain[0]

    try:
        args.cmd(rest, git_repo, args, gerrit_config)
    except RuntimeError as e:
        LOGGER.error(str(e))
        sys.exit(1)
