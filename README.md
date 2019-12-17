# Auto-SelfControl

Small utility to schedule start and stop times of
[SelfControl](https://selfcontrolapp.com).

## Purpose

Auto-SelfControl helps you to create a weekly schedule for SelfControl. You can
plan if and when SelfControl should start and stop for every weekday.

## Installation

If you already have SelfControl, start it and **back up your blacklist** as it
may be overwritten by Auto-SelfControl.

If you do not have SelfControl already installed on your system, you can
install it with [Homebrew Cask](https://caskroom.github.io/):

```sh
brew cask install selfcontrol
```

Download this repository to a directory on your system (e.g., `~/auto-selfcontrol/`).

```sh
chmod +x auto-selfcontrol.py
```

Run from this specific repository

```sh
./auto-selfcontrol.py --help
```

Or create a symlink in your `/usr/local/bin` folder to access it from anywhere.

## Usage

Edit the time configuration (see [Configuration](#configuration)) first:

```sh
./auto-selfcontrol.py config
```

When your block-schedule in [`config.json`](config.json) is ready, activate it by
running:

```sh
./auto-selfcontrol.py activate
```

__Important:__ If you change [`config.json`](config.json) later, you have to call the
`auto-selfcontrol activate` command again or Auto-SelfControl will not take the
modifications into account!

## Uninstall

Uninstall manually by removing the directory where you installed the files.

You also need to remove the automatic schedule by executing the following command in
the Terminal:

```sh
sudo rm /Library/LaunchDaemons/com.parrot-bytes.auto-selfcontrol.plist
```

## Configuration

The following listing shows an example `config.json` file that blocks every Monday
from 9am to 5.30pm and on every Tuesday from 10am to 4pm:

```json
{
    "username": "MY_USERNAME",
    "selfcontrol-path": "/Applications/SelfControl.app",
    "host-blacklist": [
        "twitter.com",
        "reddit.com"
    ],
    "block-schedules":[
        {
            "weekday": 1,
            "start-hour": 9,
            "start-minute": 0,
            "end-hour": 17,
            "end-minute": 30
        },
        {
            "weekday": 2,
            "start-hour": 10,
            "start-minute": 0,
            "end-hour": 16,
            "end-minute": 0
        }
    ]
}
```

- `username` should be the macOS username.
- `selfcontrol-path` is the absolute path to SelfControl.
- `host-blacklist` contains the list of sites that should get blacklisted as a string
  array. Please note that the blacklist in SelfControl might get overridden and should
  be __backed up__ before using Auto-SelfControl.
- `block-schedules` contains a list of schedules when SelfControl should be started.
  - The `weekday` settings specifies the day of the week when SelfControl should get
    started. Possible values are from 1 (Monday) to 7 (Sunday). If the setting is
    `null` or omitted the blocking will be scheduled for all week days.
  - `start-hour` and `start-minute` denote the time of the day when the blocking
    should start, while `end-hour` and `end-minute` specify the time it should end. The
    hours must be defined in the 24 hour digit format. If the ending time is before the
    start time, the block will last until the next day (see example below).

Please note that it is possible to create multiple schedules on the same day as long
as they are not overlapping. Have a look at the example below.

The following config blocks Twitter and Reddit every Sunday from 11pm until Monday
5am, Monday from 9am until 7pm, and Monday from 10pm to 11pm:

```json
{
    "username": "MY_USERNAME",
    "selfcontrol-path": "/Applications/SelfControl.app",
    "host-blacklist":[
        "twitter.com",
        "reddit.com"
    ],
    "block-schedules":[
        {
            "weekday": 7,
            "start-hour": 23,
            "start-minute": 0,
            "end-hour": 5,
            "end-minute": 0
        },
        {
            "weekday": 1,
            "start-hour": 9,
            "start-minute": 0,
            "end-hour": 19,
            "end-minute": 0
        },
        {
            "weekday": 1,
            "start-hour": 22,
            "start-minute": 0,
            "end-hour": 23,
            "end-minute": 0
        }
    ]
}
```

## Troubleshooting

### ImportError: No module named Foundation

This can occur if you've installed another version of Python (e.g., using Homebrew).

__Solution 1__: install `pyobjc` on your own Python version via `pip install pyobjc`.

__Solution 2__: Run Auto-SelfControl with the original Python installation from macOS
via `sudo /usr/bin/python auto-selfcontrol.py`.

[See this thread for alternative
solutions](https://stackoverflow.com/questions/1614648/importerror-no-module-named-foundation#1616361).
