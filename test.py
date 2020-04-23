from auto_selfcontrol import Schedule
import datetime


def test_active_all_weekdays():
    # Block 5am-9pm every day
    schedule = Schedule(
        weekday=None,
        start_time=datetime.time(5),
        end_time=datetime.time(21),
        block_as_whitelist=None,
        host_blacklist=None,
    )

    # 11am on a Thursday
    today = datetime.datetime(2020, 4, 23, 11)

    for i in range(7):
        day = today + datetime.timedelta(days=i)
        assert schedule.is_active(
            day
        ), f"Should be active on weekday {day.isoweekday()} {day.strftime('%A')}"


def test_active_all_weekdays_overnight():
    # Block 10pm-5am every night
    schedule = Schedule(
        weekday=None,
        start_time=datetime.time(22),
        end_time=datetime.time(5),
        block_as_whitelist=None,
        host_blacklist=None,
    )

    # 11am on a Thursday
    morning = datetime.datetime(2020, 4, 23, 11)
    # 11pm on a Thursday
    night = datetime.datetime(2020, 4, 23, 23)

    for i in range(7):
        morning_shifted = morning + datetime.timedelta(days=i)
        assert not schedule.is_active(
            morning_shifted
        ), f"Should not be active in morning on weekday {morning_shifted.isoweekday()} {morning_shifted.strftime('%A')}"
        night_shifted = night + datetime.timedelta(days=i)
        assert schedule.is_active(
            night_shifted
        ), f"Should be active in evening on weekday {night_shifted.isoweekday()} {night_shifted.strftime('%A')}"


def test_active_on_day():
    # Block from 10pm Thursday to 5am Friday
    schedule = Schedule(
        weekday=4,
        start_time=datetime.time(22),
        end_time=datetime.time(5),
        block_as_whitelist=None,
        host_blacklist=None,
    )

    thursday_morning = datetime.datetime(2020, 4, 23, 11)
    assert not schedule.is_active(thursday_morning), "Shouldn't be active"

    thursday_night = datetime.datetime(2020, 4, 23, 23)
    assert schedule.is_active(thursday_night), "Should be active at night"

    friday_morning = datetime.datetime(2020, 4, 24, 3)
    assert schedule.is_active(friday_morning), "Should be active early the next morning"

    saturday_morning = datetime.datetime(2020, 4, 25, 3)
    assert not schedule.is_active(
        saturday_morning
    ), "Should not be active early another morning"


if __name__ == "__main__":
    test_active_all_weekdays()
    test_active_all_weekdays_overnight()
    test_active_on_day()
    print("All tests passed")
