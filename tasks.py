# flake8: noqa
from pathlib import Path
from invoke import task
from pathlib import Path
import os
import shutil
import sys


QUOTE = '"' if os.name == "nt" else "'"

CHANGELOG = "CHANGELOG"
filters = ["poc", "new release", "wip", "cleanup", "!nocl"]


def filter_entries(filename):
    buffer = []
    with open(filename) as old_file:
        buffer = old_file.read().split("\n")

    with open(filename, "w") as new_file:
        for line in buffer:
            if not any(bad_word in line.lower() for bad_word in filters):
                new_file.write(line + "\n")


assert Path.cwd() == Path(__file__).parent


@task
def flake(ctx):
    """Runs flake8 against whole project"""
    ctx.run("flake8")


@task
def black(ctx):
    """Reformat code with black"""
    ctx.run("black -l130 -tpy37 .")


@task
def changelog(ctx, version=None):
    if version is not None:
        version = f"-c {version}"
    else:
        version = ""
    ctx.run(f"gcg -x -o {CHANGELOG} -O rpm {version}")
    filter_entries(CHANGELOG)

@task
def build(ctx):
    ctx.run(f"{sys.executable} setup.py sdist")


@task
def release(ctx, version=None):
    assert version != None
    changelog(ctx, version)
    ctx.run("git add CHANGELOG")
    ctx.run(f"git commit -m {QUOTE}New Release {version}{QUOTE}")
    ctx.run(f"git tag {version}")
    build(ctx)
