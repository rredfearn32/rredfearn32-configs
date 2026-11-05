import pytest
import theme_auto
from theme_auto import GSettingsError, LocationError


@pytest.fixture
def fake_gsettings(monkeypatch):
    """Replace theme_auto.gsettings with a fake.

    Call the fixture with the value the fake should return, or an exception
    instance for it to raise. Returns the list of argument tuples it was
    called with.
    """

    def install(result):
        calls = []

        def fake(*args):
            calls.append(args)
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(theme_auto, "gsettings", fake)
        return calls

    return install


class TestGetLocation:
    def test_returns_gnome_coordinates(self, fake_gsettings):
        fake_gsettings("(48.175039572102605, 11.578461000000001)")
        assert theme_auto.get_location() == (48.175039572102605, 11.578461000000001)

    @pytest.mark.parametrize(
        "output, expected",
        [
            pytest.param("(90.0, 180.0)", (90.0, 180.0), id="max"),
            pytest.param("(-90.0, -180.0)", (-90.0, -180.0), id="min"),
        ],
    )
    def test_accepts_boundary_values(self, fake_gsettings, output, expected):
        fake_gsettings(output)
        assert theme_auto.get_location() == expected

    @pytest.mark.parametrize(
        "output",
        [
            pytest.param("(91,181)", id="gnome-default"),
            pytest.param("(90.1, 0.0)", id="lat-too-high"),
            pytest.param("(0.0, -180.1)", id="lon-too-low"),
        ],
    )
    def test_out_of_range_raises(self, fake_gsettings, output):
        fake_gsettings(output)
        with pytest.raises(LocationError, match="out of range"):
            theme_auto.get_location()

    @pytest.mark.parametrize(
        "output, cause",
        [
            pytest.param("", SyntaxError, id="empty"),
            pytest.param("garbage", ValueError, id="not-a-literal"),
            pytest.param("(1.0,)", ValueError, id="too-few-values"),
            pytest.param("(1.0, 2.0, 3.0)", ValueError, id="too-many-values"),
            pytest.param("1.0", TypeError, id="not-a-tuple"),
            pytest.param("('a', 'b')", TypeError, id="not-numbers"),
        ],
    )
    def test_malformed_output_raises(self, fake_gsettings, output, cause):
        fake_gsettings(output)
        with pytest.raises(LocationError, match="could not parse") as exc_info:
            theme_auto.get_location()
        assert type(exc_info.value.__cause__) is cause

    def test_gsettings_failure_raises(self, fake_gsettings):
        error = GSettingsError("boom")
        fake_gsettings(error)
        with pytest.raises(
            LocationError, match="could not read location: boom"
        ) as exc_info:
            theme_auto.get_location()
        assert exc_info.value.__cause__ is error

    def test_reads_night_light_coordinates(self, fake_gsettings):
        calls = fake_gsettings("(48.175, 11.578)")
        theme_auto.get_location()
        assert calls == [
            (
                "get",
                "org.gnome.settings-daemon.plugins.color",
                "night-light-last-coordinates",
            )
        ]
