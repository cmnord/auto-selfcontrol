# Auto-SelfControl

OSX utility to automatically start / stop [SelfControl](http://selfcontrolapp.com).

## Install
- Download Auto-SelfControl and copy/extract it to a directory on your Mac.
- Edit the config.json (see [Configuration](#Configuration) first).
- Open Terminal.app and cd to the directory.
- Execute `sudo python auto-selfcontrol.py` to install Auto-SelfControl with the block-schedule defined in [config.json](config.json). __Important:__ If you change [config.json](config.json) later, you have to call the installation command again or Auto-SelfControl might not start at the right time!

## Configuration
The following listing shows an example config.json file that blocks reddit.com and youtube.com every Monday from 9am to 5.30pm and netflix.com on every Tuesday from 10am to 4pm:
```
    {
        "username": "MY_USERNAME",
        "selfcontrol-path": "/Applications/SelfControl.app",
        "legacy-mode": true,
        "block-schedules":[
            {
                "weekday": 1,
                "start-hour": 9,
                "start-minute": 0,
                "end-hour": 17,
                "end-minute": 30,
                "block-as-whitelist": false,
                "host-blacklist": [
                    "reddit.com",
                    "youtube.com"
                ]
            },
            {
                "weekday": 2,
                "start-hour": 10,
                "start-minute": 0,
                "end-hour": 16,
                "end-minute": 0,
                "block-as-whitelist": false,
                "host-blacklist": [
                    "netflix.com"
                ]
            }
        ]
    }
```
- _username_ should be the Mac OS X username.
- _selfcontrol-path_ is the absolute path to [SelfControl](http://selfcontrolapp.com).
- _legacy-mode_ is at the moment always required to be true, but might be omitted in future versions of SelfControl.
- _block-schedules_ contains a list of schedules when SelfControl should be started. 
    * The _weekday_ settings specifies the day of the week when SelfControl should get started. Possible values are from 1 (Monday) to 7 (Sunday). 
    * _start-hour_ and _start-minute_ denote the time of the day when the blocking should start, while _end-hour_ and _end-minute_ specify the time it should end. If the ending time is before the start time, the block will last until the next day (see example below).
    * Finally, _host-blacklist_ contains the list of sites that should get blacklisted. However, this last setting is optional and should be omitted if all schedules should block the same list of sites. In this case it is recommended to use SelfControl directly to create a blacklist and set this setting to `null` in the config.json file.

    Please note that it is possible to create multiple schedules on the same day, as long as they are not overlapping. _block-as-whitelist_ specifies whether a whitelist or blacklist (recommended) blocking should be used. Have a look at the example below.

The following listing shows another example without custom blacklists that blocks every Sunday from 11pm til Monday 5am and from Monday 9am until 7pm:
```
    {
        "username": "MY_USERNAME",
        "selfcontrol-path": "/Applications/SelfControl.app",
        "legacy-mode": true,
        "block-schedules":[
            {
                "weekday": 1,
                "start-hour": 9,
                "start-minute": 0,
                "end-hour": 19,
                "end-minute": 0,
                "block-as-whitelist": false,
                "host-blacklist": null
            },
            {
                "weekday": 7,
                "start-hour": 23,
                "start-minute": 0,
                "end-hour": 5,
                "end-minute": 0,
                "block-as-whitelist": false,
                "host-blacklist": null
            }
        ]
    }
```

## Uninstall
- Delete the installation directory of Auto-SelfControl
- Execute in the Terminal.app `sudo rm /Library/LaunchDaemons/com.parrot-bytes.auto-selfcontrol.plist`