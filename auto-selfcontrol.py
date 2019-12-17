#!/usr/bin/env python

from argparse import ArgumentParser
import datetime
from dataclasses import dataclass
from Foundation import (
    NSUserDefaults,
    CFPreferencesSetAppValue,
    CFPreferencesAppSynchronize,
    NSDate,
)
import json
import os
from pwd import getpwnam
import subprocess
from typing import Any, Dict, Iterator, List, Optional, Sequence


LAUNCHLIST_PATH = "/Library/LaunchDaemons/com.parrot-bytes.auto-selfcontrol.plist"
GITHUB_CONFIG = "https://raw.githubusercontent.com/cmnord/auto-selfcontrol/master/config.json"
HOME = os.environ["HOME"]
CONFIG_DIR = os.path.join(HOME, "dev/auto-selfcontrol")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class AutoSelfControlException(Exception):
    pass


class AlreadyRunningException(AutoSelfControlException):
    """ Raised if self-control is already running. """

    pass


class NoScheduleActiveException(AutoSelfControlException):
    """ Raised if there is no schedule active for this time frame. """

    pass


class ConfigException(AutoSelfControlException):
    """ Raised if the config file does not follow the schema. """

    pass


@dataclass
class Schedule:
    weekday: Optional[int]
    start_hour: int
    start_minute: int
    end_hour: int
    end_minute: int
    block_as_whitelist: Optional[bool]
    host_blacklist: Optional[List[str]]

    @staticmethod
    def from_config(config: Dict[str, Any]) -> "Schedule":
        return Schedule(
            weekday=config.get("weekday"),
            start_hour=config["start-hour"],
            start_minute=config["start-minute"],
            end_hour=config["end-hour"],
            end_minute=config["end-minute"],
            block_as_whitelist=config.get("block-as-whitelist"),
            host_blacklist=config.get("host-blacklist"),
        )

    def weekdays(self) -> Sequence[int]:
        """Return a list of weekdays the specified schedule is active."""
        return [self.weekday] if self.weekday is not None else range(1, 8)

    def is_active(self) -> bool:
        """Check if we are right now in the provided schedule or not."""
        now = datetime.datetime.today()
        starttime = datetime.datetime(
            now.year, now.month, now.day, self.start_hour, self.start_minute
        )
        endtime = datetime.datetime(
            now.year, now.month, now.day, self.end_hour, self.end_minute
        )
        duration = endtime - starttime

        for weekday in self.weekdays():
            weekday_diff = now.isoweekday() % 7 - weekday % 7
            if weekday_diff == 0:
                # schedule's weekday is today
                return (
                    starttime <= now and endtime >= now
                    if duration.days == 0
                    else starttime <= now
                )
            if weekday_diff == 1 or weekday_diff == -6:
                # schedule's weekday was yesterday
                return duration.days != 0 and now <= endtime
        return False

    def duration_minutes(self) -> int:
        """Return the minutes left until the schedule's end-hour and end-minute are reached."""
        now = datetime.datetime.today()
        endtime = datetime.datetime(
            now.year, now.month, now.day, self.end_hour, self.end_minute
        )
        duration = endtime - now
        return int(round(duration.seconds / 60.0))


@dataclass
class Config:
    username: str
    selfcontrol_path: str
    block_schedules: List[Schedule]
    host_blacklist: Optional[List[str]]
    legacy_mode: Optional[bool]

    @staticmethod
    def from_file(filename: str) -> "Config":
        """ Load JSON configuration file. The latter configs overwrite the previous
        configs. """
        with open(filename, "rt") as f:
            config = json.load(f)

        if "username" not in config:
            raise ConfigException("No username specified in config.")
        if config["username"] not in get_osx_usernames():
            raise ConfigException(
                f"Username '{config['username']}' unknown. Please use your OSX "
                "username instead. If you have trouble finding it, just enter the "
                "command 'whoami' in your terminal."
            )
        if "selfcontrol-path" not in config:
            raise ConfigException(
                "The setting 'selfcontrol-path' is required and must point to the "
                "location of SelfControl."
            )
        if not os.path.exists(config["selfcontrol-path"]):
            raise ConfigException(
                "The setting 'selfcontrol-path' does not point to the correct "
                "location of SelfControl. Please make sure to use an absolute path and "
                "include the '.app' extension, e.g. /Applications/SelfControl.app"
            )
        if "block-schedules" not in config:
            raise ConfigException("The setting 'block-schedules' is required.")
        if len(config["block-schedules"]) == 0:
            raise ConfigException(
                "You need at least one schedule in 'block-schedules'."
            )
        if "host-blacklist" not in config:
            print(
                "WARNING: It is not recommended to directly use SelfControl's "
                "blacklist. Please use the 'host-blacklist' setting instead."
            )

        return Config(
            username=config["username"],
            selfcontrol_path=config["selfcontrol-path"],
            block_schedules=[
                Schedule.from_config(s) for s in config["block-schedules"]
            ],
            host_blacklist=config.get("host-blacklist"),
            legacy_mode=config.get("legacy-mode"),
        )

    def launchscript_startintervals(self) -> Iterator[str]:
        """Return the string of the launchscript start intervals."""
        # entries = list()
        for schedule in self.block_schedules:
            for weekday in schedule.weekdays():
                yield f"""<dict>
                        <key>Weekday</key>
                        <integer>{weekday}</integer>
                        <key>Minute</key>
                        <integer>{schedule.start_minute}</integer>
                        <key>Hour</key>
                        <integer>{schedule.start_hour}</integer>
                    </dict>
                    """

    def launchscript(self) -> str:
        """Return the string of the launchscript."""
        path = os.path.realpath(__file__)
        start_intervals = "".join(self.launchscript_startintervals())
        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>com.parrot-bytes.auto-selfcontrol</string>
            <key>ProgramArguments</key>
            <array>
                <string>/usr/bin/python</string>
                <string>{path}</string>
                <string>-r</string>
            </array>
            <key>StartCalendarInterval</key>
            <array>
                {start_intervals}</array>
            <key>RunAtLoad</key>
            <true/>
        </dict>
        </plist>"""

    def install(self) -> int:
        """ Installs auto-selfcontrol """
        # Check for existing plist
        if os.path.exists(LAUNCHLIST_PATH):
            subprocess.call(["launchctl", "unload", "-w", LAUNCHLIST_PATH])
            os.unlink(LAUNCHLIST_PATH)
            print("> Removed previous installation files")

        launchplist_script = self.launchscript()

        with open(LAUNCHLIST_PATH, "w") as f:
            f.write(launchplist_script)

        return subprocess.call(["launchctl", "load", "-w", LAUNCHLIST_PATH])

    def run(self) -> int:
        """ Start self-control with custom parameters, depending on the weekday and
        the config. Return the duration in minutes for which self-control will run.
        """
        if running(self.username):
            raise AlreadyRunningException("SelfControl is already running.")

        try:
            schedule = next(s for s in self.block_schedules if s.is_active())
        except StopIteration:
            raise NoScheduleActiveException(
                "No schedule is active at the moment. Shutting down."
            )

        duration = schedule.duration_minutes()
        set_selfcontrol_setting("BlockDuration", duration, self.username)
        set_selfcontrol_setting(
            "BlockAsWhitelist",
            1 if schedule.block_as_whitelist is True else 0,
            self.username,
        )

        if schedule.host_blacklist is not None:
            set_selfcontrol_setting(
                "HostBlacklist", schedule.host_blacklist, self.username
            )
        elif self.host_blacklist is not None:
            set_selfcontrol_setting("HostBlacklist", self.host_blacklist, self.username)

        # In legacy mode manually set the BlockStartedDate, this should not be required anymore in future versions
        # of SelfControl.
        if self.legacy_mode is True:
            set_selfcontrol_setting("BlockStartedDate", NSDate.date(), self.username)

        # Start SelfControl
        # TODO: injection vulnerability
        user_id = str(getpwnam(self.username).pw_uid)
        os.system(
            f"{self.selfcontrol_path}/Contents/MacOS/org.eyebeam.SelfControl {user_id} --install"
        )

        return duration


def running(username: str) -> bool:
    """Check if self-control is already running."""
    defaults = get_selfcontrol_settings(username)
    return "BlockStartedDate" in defaults and not NSDate.distantFuture().isEqualToDate_(
        defaults["BlockStartedDate"]
    )


def set_selfcontrol_setting(key: str, value: Any, username: str) -> None:
    """Set a single default setting of SelfControl for the provided username."""
    NSUserDefaults.resetStandardUserDefaults()
    originalUID = os.geteuid()
    os.seteuid(getpwnam(username).pw_uid)
    CFPreferencesSetAppValue(key, value, "org.eyebeam.SelfControl")
    CFPreferencesAppSynchronize("org.eyebeam.SelfControl")
    NSUserDefaults.resetStandardUserDefaults()
    os.seteuid(originalUID)


def get_selfcontrol_settings(username: str) -> Dict[str, Any]:
    """Return all default settings of SelfControl for the provided username."""
    NSUserDefaults.resetStandardUserDefaults()
    originalUID = os.geteuid()
    os.seteuid(getpwnam(username).pw_uid)
    defaults = NSUserDefaults.standardUserDefaults()
    defaults.addSuiteNamed_("org.eyebeam.SelfControl")
    defaults.synchronize()
    result = defaults.dictionaryRepresentation()
    NSUserDefaults.resetStandardUserDefaults()
    os.seteuid(originalUID)
    return result


def get_osx_usernames() -> List[str]:
    output = subprocess.check_output(["dscl", ".", "list", "/users"])
    return [s.strip().decode("utf-8") for s in output.splitlines()]


def activate() -> None:
    if os.geteuid() != 0:
        filename = os.path.realpath(__file__)
        raise AutoSelfControlException(
            f"Please make sure to run the script with elevated rights, such as:\nsudo python {filename} "
        )

    config = Config.from_file(CONFIG_FILE)

    print("> Starting installation of Auto-SelfControl...")
    if config.install() != 0:
        print("> Installation failed.")
        return
    print("> Installed.")

    print("> Starting SelfControl (this could take a few minutes)...")
    try:
        duration = config.run()
        print(f"> SelfControl was started for {duration} minute(s).")
    except (AlreadyRunningException, NoScheduleActiveException) as exc:
        print(f"> {exc}")
        return

def config() -> int:
    # If no "config.json" in ~/.config/auto-selfcontrol/
    if not os.path.exists(CONFIG_FILE):
        # If existing "config.json" in the cwd, copy it
        if "config.json" in os.listdir("."):
            subprocess.call(["cp", "config.json", CONFIG_FILE])
            print(f"> Copied config.json from the current directory to {CONFIG_FILE}")
        else:
            # else download sample config from github repository
            subprocess.call(["curl", "-L", "-s", GITHUB_CONFIG, "-o", CONFIG_FILE])
            print(f"> Downloaded sample configuration to {CONFIG_FILE}")

    print(f"> Opening {CONFIG_FILE}")
    # Opening with default editor set as $EDITOR
    if "EDITOR" in os.environ:
        return subprocess.call([os.environ["EDITOR"], CONFIG_FILE])
    # Or with default GUI text editor (txt files > Open with...)
    return subprocess.call(["open", "-t", CONFIG_FILE])

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Auto-SelfControl (c) Andreas Grill\nSmall utility to schedule "
        "start and stop times of SelfControl. More instructions at "
        "https://github.com/cmnord/auto-selfcontrol"
    )
    parser.add_argument(
        "action",
        choices=("config", "activate"),
        help="Open the schedule [config] file in a text editor to set up weekly "
        "parameters or [activate] the automatic start/stop of SelfControl according to "
        "schedules defined in configuration",
    )

    args = parser.parse_args()
    if args.action == "config":
        config()
    elif args.action == "activate":
        activate()
