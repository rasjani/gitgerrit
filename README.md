git-gerrit
==========

Command line to to interact with gerrit and its ci integrations.. Made for internal use but
could be useful for others too.


## Installation

`pip install gitgerrit`

After the package has been installed, its available via `git gerrit`.


## Usage

At this time, git gerrit has 3 sub commands. `runverify` `topic` & `abandon`

Each of these subcommands operate at the current git branch's head commit unless you pass  `--commit N` or `--changeid N` flags.

If also pass `--support-chain` flag, all operations are targetting whole commit chains that.

you can also specify logging level via --loglevel=$level flag.

## Configuration

You must provide following settings in your local or global git configuration:
```
[gerrit]
  token = $gerrit_restapi_token
  user = $gerrit_username
  host = $gerrit_hostname
```

Or, you can set corresponding environment variables: GERRIT_TOKEN, GERRIT_USER, GERRIT_HOST

### runverify

`git gerrit runverify` will add a comment to latest revision of current comment if it ha been published into gerrit.
If you want to add the commit to some other change, you can use `--changeid` or `--commit`

If you want to to check the state votes of the change request, append `--check` flag to `runverify`

### abandon

`git gerrit abandon` will abandon current change request if its already in gerrit. If you have been working on a commit chain and
you would like to abandon it as  whole:  `git gerrit --support-chain abandon`

### topic

`git gerrit topic --check` will show all the commits/changes in gerrit in your current commit chain.

If you wish to set a topic to a single commit:

`git gerrit topic --set newtopic`

Default value for topic is always "noci".

`git gerrit --support-chain topic` will set topic of all changes in your commit chain except the HEAD into "noci". Same command
could be also written as `git gerrit --support-chain topic --set noci`


