from datetime import UTC, date, datetime, timedelta

import pytest
from theme_auto import get_sunrise_sunset

# (lat, lon)
MUNICH = (48.137284, 11.575498)
NEW_YORK = (40.712776, -74.005974)
SYDNEY = (-33.868820, 151.209296)
REYKJAVIK = (64.146582, -21.942635)
SINGAPORE = (1.352083, 103.819836)

Q1 = date(2026, 3, 20)
Q2 = date(2026, 6, 21)
Q3 = date(2026, 9, 23)
Q4 = date(2026, 12, 21)

# The script uses a NOAA approximation, so allow some drift. The error grows at
# high latitudes (Reykjavik's Q3 sunset is ~5 min off), hence 6 minutes.
TOLERANCE = timedelta(minutes=6)


def utc(*args):
    return datetime(*args, tzinfo=UTC)


# Expected times are from the `astral` library (NOAA's full solar algorithm),
# rounded to the nearest minute, in UTC. Each Qn date is that quarter's
# equinox or solstice. Events can fall on the previous or next UTC day for
# locations far from Greenwich, e.g. Sydney's sunrise or New York's Q2 sunset.
@pytest.mark.parametrize(
    "location, day, expected_sunrise, expected_sunset",
    [
        pytest.param(
            MUNICH,
            Q1,
            utc(2026, 3, 20, 5, 17),
            utc(2026, 3, 20, 17, 26),
            id="munich-q1",
        ),
        pytest.param(
            MUNICH,
            Q2,
            utc(2026, 6, 21, 3, 14),
            utc(2026, 6, 21, 19, 17),
            id="munich-q2",
        ),
        pytest.param(
            MUNICH, Q3, utc(2026, 9, 23, 5, 2), utc(2026, 9, 23, 17, 10), id="munich-q3"
        ),
        pytest.param(
            MUNICH,
            Q4,
            utc(2026, 12, 21, 7, 2),
            utc(2026, 12, 21, 15, 22),
            id="munich-q4",
        ),
        pytest.param(
            NEW_YORK,
            Q1,
            utc(2026, 3, 20, 11, 0),
            utc(2026, 3, 20, 23, 8),
            id="new_york-q1",
        ),
        pytest.param(
            NEW_YORK,
            Q2,
            utc(2026, 6, 21, 9, 25),
            utc(2026, 6, 22, 0, 30),
            id="new_york-q2",
        ),
        pytest.param(
            NEW_YORK,
            Q3,
            utc(2026, 9, 23, 10, 45),
            utc(2026, 9, 23, 22, 51),
            id="new_york-q3",
        ),
        pytest.param(
            NEW_YORK,
            Q4,
            utc(2026, 12, 21, 12, 17),
            utc(2026, 12, 21, 21, 32),
            id="new_york-q4",
        ),
        pytest.param(
            SYDNEY, Q1, utc(2026, 3, 19, 19, 58), utc(2026, 3, 20, 8, 7), id="sydney-q1"
        ),
        pytest.param(
            SYDNEY, Q2, utc(2026, 6, 20, 21, 0), utc(2026, 6, 21, 6, 54), id="sydney-q2"
        ),
        pytest.param(
            SYDNEY,
            Q3,
            utc(2026, 9, 22, 19, 44),
            utc(2026, 9, 23, 7, 52),
            id="sydney-q3",
        ),
        pytest.param(
            SYDNEY,
            Q4,
            utc(2026, 12, 20, 18, 41),
            utc(2026, 12, 21, 9, 5),
            id="sydney-q4",
        ),
        pytest.param(
            REYKJAVIK,
            Q1,
            utc(2026, 3, 20, 7, 29),
            utc(2026, 3, 20, 19, 43),
            id="reykjavik-q1",
        ),
        pytest.param(
            REYKJAVIK,
            Q2,
            utc(2026, 6, 21, 2, 56),
            utc(2026, 6, 22, 0, 3),
            id="reykjavik-q2",
        ),
        pytest.param(
            REYKJAVIK,
            Q3,
            utc(2026, 9, 23, 7, 14),
            utc(2026, 9, 23, 19, 25),
            id="reykjavik-q3",
        ),
        pytest.param(
            REYKJAVIK,
            Q4,
            utc(2026, 12, 21, 11, 23),
            utc(2026, 12, 21, 15, 29),
            id="reykjavik-q4",
        ),
        pytest.param(
            SINGAPORE,
            Q1,
            utc(2026, 3, 19, 23, 9),
            utc(2026, 3, 20, 11, 15),
            id="singapore-q1",
        ),
        pytest.param(
            SINGAPORE,
            Q2,
            utc(2026, 6, 20, 23, 1),
            utc(2026, 6, 21, 11, 12),
            id="singapore-q2",
        ),
        pytest.param(
            SINGAPORE,
            Q3,
            utc(2026, 9, 22, 22, 54),
            utc(2026, 9, 23, 11, 0),
            id="singapore-q3",
        ),
        pytest.param(
            SINGAPORE,
            Q4,
            utc(2026, 12, 20, 23, 1),
            utc(2026, 12, 21, 11, 4),
            id="singapore-q4",
        ),
    ],
)
class TestGetSunriseSunset:
    def test_for_locations(self, location, day, expected_sunrise, expected_sunset):
        lat, lon = location
        sunrise, sunset = get_sunrise_sunset(day, lat, lon)
        assert abs(sunrise - expected_sunrise) <= TOLERANCE
        assert abs(sunset - expected_sunset) <= TOLERANCE
