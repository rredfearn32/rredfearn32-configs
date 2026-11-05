import os
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import theme_auto
from theme_auto import GSettingsError, LocationError

SCRIPT = Path(theme_auto.__file__)

# (lat, lon) as the strings GNOME stores them in gsettings.
MUNICH = "(48.137284, 11.575498)"
NEW_YORK = "(40.712776, -74.005974)"
SYDNEY = "(-33.868820, 151.209296)"

LIGHT = "default"
DARK = "prefer-dark"


def utc(*args):
    return datetime(*args, tzinfo=UTC)


@pytest.fixture
def fake_gsettings(monkeypatch):
    """Replace theme_auto.gsettings with a fake that answers per key.

    `location` and `scheme` are the outputs for the two `get` calls. Either
    can be an exception instance, which is raised. `set_error` is raised by
    the `set` call. Returns the list of argument tuples it was called with.
    """

    def install(location=MUNICH, scheme=f"'{LIGHT}'", set_error=None):
        calls = []

        def fake(*args):
            calls.append(args)
            if args[0] == "get" and args[2] == "night-light-last-coordinates":
                result = location
            elif args[0] == "get" and args[2] == "color-scheme":
                result = scheme
            else:
                result = set_error or ""
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(theme_auto, "gsettings", fake)
        return calls

    return install


@pytest.fixture
def fixed_sun(monkeypatch):
    """Make every day's sunrise and sunset the given UTC times on that day."""

    def install(rise_time, set_time):
        def fake(day, lat, lon):
            base = datetime(day.year, day.month, day.day, tzinfo=UTC)
            return base + rise_time, base + set_time

        monkeypatch.setattr(theme_auto, "get_sunrise_sunset", fake)

    return install


@pytest.fixture
def local_tz():
    """Set the process time zone for the test, then restore it."""
    old = os.environ.get("TZ")

    def install(name):
        os.environ["TZ"] = name
        time.tzset()

    yield install
    if old is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = old
    time.tzset()


def set_calls(calls):
    return [c for c in calls if c[0] == "set"]


def wanted_scheme(calls, scheme):
    """The scheme main() wants, given the current scheme it was shown."""
    sets = set_calls(calls)
    return sets[0][3] if sets else scheme


class TestSwitching:
    def test_daytime_switches_dark_to_light(self, fake_gsettings):
        calls = fake_gsettings(scheme=f"'{DARK}'")
        theme_auto.main(utc(2026, 6, 21, 12, 0))
        assert set_calls(calls) == [
            ("set", "org.gnome.desktop.interface", "color-scheme", LIGHT)
        ]

    def test_night_switches_light_to_dark(self, fake_gsettings):
        calls = fake_gsettings(scheme=f"'{LIGHT}'")
        theme_auto.main(utc(2026, 6, 21, 2, 0))
        assert set_calls(calls) == [
            ("set", "org.gnome.desktop.interface", "color-scheme", DARK)
        ]

    @pytest.mark.parametrize(
        "now, scheme",
        [
            pytest.param(utc(2026, 6, 21, 12, 0), LIGHT, id="day"),
            pytest.param(utc(2026, 6, 21, 2, 0), DARK, id="night"),
        ],
    )
    def test_already_correct_does_not_set(self, fake_gsettings, now, scheme):
        # gsettings returns the value quoted, so this also checks the quotes
        # are stripped before comparing.
        calls = fake_gsettings(scheme=f"'{scheme}'")
        theme_auto.main(now)
        assert set_calls(calls) == []

    def test_unknown_current_value_is_replaced(self, fake_gsettings):
        calls = fake_gsettings(scheme="'prefer-light'")
        theme_auto.main(utc(2026, 6, 21, 12, 0))
        assert set_calls(calls) == [
            ("set", "org.gnome.desktop.interface", "color-scheme", LIGHT)
        ]


class TestBoundaries:
    @pytest.mark.parametrize(
        "now, expected",
        [
            pytest.param(
                utc(2026, 6, 21, 6, 0) - timedelta(microseconds=1),
                DARK,
                id="just-before-sunrise",
            ),
            pytest.param(utc(2026, 6, 21, 6, 0), LIGHT, id="at-sunrise"),
            pytest.param(
                utc(2026, 6, 21, 18, 0) - timedelta(microseconds=1),
                LIGHT,
                id="just-before-sunset",
            ),
            pytest.param(utc(2026, 6, 21, 18, 0), DARK, id="at-sunset"),
        ],
    )
    def test_day_is_sunrise_inclusive_sunset_exclusive(
        self, fake_gsettings, fixed_sun, now, expected
    ):
        fixed_sun(timedelta(hours=6), timedelta(hours=18))
        scheme = DARK if expected == LIGHT else LIGHT
        calls = fake_gsettings(scheme=f"'{scheme}'")
        theme_auto.main(now)
        assert wanted_scheme(calls, scheme) == expected


class TestUtcDayCrossing:
    # Times are from test_get_sunrise_sunset.py: these events fall on a
    # different UTC day from the local day they belong to.
    @pytest.mark.parametrize(
        "location, now",
        [
            # 08:00 local on the 21st. Sunrise for the 21st is 06-20 21:00 UTC,
            # so only the +1 day offset finds it.
            pytest.param(SYDNEY, utc(2026, 6, 20, 22, 0), id="sydney-next-day"),
            # Sunset for the 21st is 06-22 00:30 UTC, so only the -1 day
            # offset finds it.
            pytest.param(NEW_YORK, utc(2026, 6, 22, 0, 15), id="new_york-prev-day"),
        ],
    )
    def test_is_day(self, fake_gsettings, location, now):
        calls = fake_gsettings(location=location, scheme=f"'{DARK}'")
        theme_auto.main(now)
        assert wanted_scheme(calls, DARK) == LIGHT


class TestErrors:
    def test_location_error_propagates_before_reading_scheme(self, fake_gsettings):
        calls = fake_gsettings(location="(91,181)")
        with pytest.raises(LocationError):
            theme_auto.main(utc(2026, 6, 21, 12, 0))
        assert [c for c in calls if "color-scheme" in c] == []

    def test_set_failure_propagates(self, fake_gsettings):
        error = GSettingsError("boom")
        fake_gsettings(scheme=f"'{DARK}'", set_error=error)
        with pytest.raises(GSettingsError) as exc_info:
            theme_auto.main(utc(2026, 6, 21, 12, 0))
        assert exc_info.value is error

    def test_script_exits_1_and_prints_error(self, tmp_path):
        fake = tmp_path / "gsettings"
        fake.write_text("#!/bin/sh\necho boom >&2\nexit 3\n")
        fake.chmod(0o755)
        env = {**os.environ, "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True, env=env
        )
        assert result.returncode == 1
        assert "could not read location" in result.stderr
        assert "boom" in result.stderr


class TestOutput:
    def test_prints_switched_when_changed(self, fake_gsettings, capsys):
        fake_gsettings(scheme=f"'{DARK}'")
        theme_auto.main(utc(2026, 6, 21, 12, 0))
        assert f"switched to {LIGHT}" in capsys.readouterr().out

    def test_does_not_print_switched_when_unchanged(self, fake_gsettings, capsys):
        fake_gsettings(scheme=f"'{LIGHT}'")
        theme_auto.main(utc(2026, 6, 21, 12, 0))
        assert "switched" not in capsys.readouterr().out

    def test_log_shows_matching_days_times(
        self, fake_gsettings, monkeypatch, local_tz, capsys
    ):
        # Give each day distinct times so the printed day is visible:
        # the 21st's window is 06-20 21:00 to 06-21 07:00 UTC (as in Sydney),
        # and other days are shifted by an hour per day.
        def fake_sun(day, lat, lon):
            shift = timedelta(hours=day.day - 21)
            rise = utc(2026, 6, 20, 21, 0) + timedelta(days=day.day - 21) + shift
            return rise, rise + timedelta(hours=10)

        monkeypatch.setattr(theme_auto, "get_sunrise_sunset", fake_sun)
        local_tz("UTC")
        fake_gsettings(location=SYDNEY, scheme=f"'{LIGHT}'")
        theme_auto.main(utc(2026, 6, 20, 22, 0))
        assert "sunrise 21:00, sunset 07:00" in capsys.readouterr().out
