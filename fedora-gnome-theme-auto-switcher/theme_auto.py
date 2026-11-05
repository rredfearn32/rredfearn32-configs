#!/usr/bin/python3
import ast
import math
import subprocess
import sys
from datetime import UTC, datetime, timedelta


def get_sunrise_sunset(day, lat, lon):
    # NOAA approximation. Returns (sunrise, sunset) as UTC datetimes.
    n = day.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(g)
        - 0.032077 * math.sin(g)
        - 0.014615 * math.cos(2 * g)
        - 0.040849 * math.sin(2 * g)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(g)
        + 0.070257 * math.sin(g)
        - 0.006758 * math.cos(2 * g)
        + 0.000907 * math.sin(2 * g)
        - 0.002697 * math.cos(3 * g)
        + 0.00148 * math.sin(3 * g)
    )
    lat_r = math.radians(lat)
    cos_ha = math.cos(math.radians(90.833)) / (
        math.cos(lat_r) * math.cos(decl)
    ) - math.tan(lat_r) * math.tan(decl)
    ha = math.degrees(math.acos(max(-1.0, min(1.0, cos_ha))))
    rise_min = 720 - 4 * (lon + ha) - eqtime
    set_min = 720 - 4 * (lon - ha) - eqtime
    base = datetime(day.year, day.month, day.day, tzinfo=UTC)
    return base + timedelta(minutes=rise_min), base + timedelta(minutes=set_min)


class GSettingsError(Exception):
    pass


def gsettings(*args):
    r = subprocess.run(["gsettings", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise GSettingsError(
            f"gsettings {' '.join(args)} failed "
            f"(exit {r.returncode}): {r.stderr.strip()}"
        )
    return r.stdout.strip()


class LocationError(Exception):
    pass


def get_location():
    # Use GNOME's cached location (from GeoClue/Night Light). Raises LocationError
    # if it can't be read or isn't valid.
    try:
        out = gsettings(
            "get",
            "org.gnome.settings-daemon.plugins.color",
            "night-light-last-coordinates",
        )
    except GSettingsError as e:
        raise LocationError(f"could not read location: {e}") from e
    try:
        lat, lon = ast.literal_eval(out)
        in_range = abs(lat) <= 90 and abs(lon) <= 180
    except (ValueError, SyntaxError, TypeError) as e:
        raise LocationError(
            f"could not parse location from gsettings output {out!r}"
        ) from e
    if not in_range:
        # GNOME's default is (91, 181) until a location has been detected.
        raise LocationError(
            f"location {out} is out of range; GNOME may not have detected a "
            "location yet (check that Location Services is enabled)"
        )
    return lat, lon


def main(now=None):
    now = now or datetime.now(UTC)
    lat, lon = get_location()
    daytime = False
    for offset in (-1, 0, 1):
        day = now.date() + timedelta(days=offset)
        srise, sset = get_sunrise_sunset(day, lat, lon)
        if srise <= now < sset:
            daytime = True
            break
    wanted = "default" if daytime else "prefer-dark"

    current = gsettings("get", "org.gnome.desktop.interface", "color-scheme").strip("'")
    print(
        f"sunrise {srise.astimezone():%H:%M}, sunset {sset.astimezone():%H:%M}, "
        f"now {'day' if daytime else 'night'}, current={current}, wanted={wanted}"
    )

    if current != wanted:
        gsettings("set", "org.gnome.desktop.interface", "color-scheme", wanted)
        print(f"switched to {wanted}")


if __name__ == "__main__":
    try:
        main()
    except (GSettingsError, LocationError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
