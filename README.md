git-gerrit
==========

Command line to to interact with gerrit codereview service and its ci integrations. Made for internal use but
could be useful for others too.


## Installation

`pip install gitgerrit`

After the package has been installed, its available via `git gerrit`.

## Configuration

* Generate HTTP Password in Gerrit web ui.
* `git config --add gerrit.host hostname.of.your.gerrit.instance`
* `git config --add gerrit.user your_user_name`
* `git config --add gerrit.token your_http_password`

Or alternative, you can set the same values into following environment variables:

* GERRIT_HOST
* GERRIT_USER
* GERRIT_TOKEN

If you need to modify the the comment used by runverify action, you can optionally add env GERRIT_TRIGGER or gerrit.trigger
git configuration option.

## Usage


*git-gerrit* either works on current commit of the checked out repository if no `--commit` or `--changeid` wherent provided.

By default, *git-gerrit* operates on a single commit. If you want to apply your actions to each commit that are submitted
together, provide `--support-chain` argument before action.

you can also specify logging level via --loglevel=$level flag.

After the optional paremters that affect what change requests are being operated on, you need to provide the keyword that defines
what action is taken against change(s)

## Actions

### runverify
Can either print out the current votes on latest revision of change(s) or adds "runverify" message to the latest revision to
trigger a ci build of your current changes.

For more details: `git gerrit runverify -h`
### topic
Can set or get topic into change(s)get or set topic on change(s)

For more details: `git gerrit runverify -h`
### hashtag
Get, add or remove hashtag(s) on change(s). `--add` and  `--del` flags be added to command line multiple times in order to add
or remove multiple hashtags in one call. If no hashtags are given, defaults to adding a current branch name to change(s) list
of hashtags

For more details: `git gerrit hashtag-h`
### wip
Marks change(s) as Work-In-Progress indicating that no reviewing required at the moment.

For more details: `git gerrit wip -h`
### ready
Marks change(s) as Ready-For-Review indicating that your changes are ready for a review

For more details: `git gerrit ready -h`
### private
Marks change(s) as Private. Only people who have been added as reviewers can see the change(s)

For more details: `git gerrit private -h`
### public
Marks change(s) as Public. Everyone with the access to the project can then see your change(s)

For more details: `git gerrit public -h`
### prepare
Prepares change(s) to be ready for merge. This is a group actions:
 * Marks changes(s) as Ready-For-Review
 * Marks changes(s) as Public
 * Changes all changes(s) expect HEAD topic's into NOCI to avoid multiple builds when merged.
 * Adds HEAD's topic as hashtag to change(s)

For more details: `git gerrit prepare -h`
### abandon
Abandon change(s)
For more details: `git gerrit abandon -h`

