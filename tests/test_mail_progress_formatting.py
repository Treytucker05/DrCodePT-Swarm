from agent.autonomous.tools.mail_yahoo_imap_executor import (
    _format_progress_line,
    _format_timing_line,
)


def test_format_progress_line_percent_and_current():
    line = _format_progress_line(
        label="Scanning folders",
        count=12,
        total=41,
        current="PowerHouseATX/2018",
    )
    assert (
        line
        == "[PROGRESS] Scanning folders: 12/41 (29%) current=PowerHouseATX/2018"
    )


def test_format_timing_line_eta():
    line = _format_timing_line(
        elapsed=12.4,
        count=4,
        total=10,
        unit_label="folder",
    )
    assert line == "[PROGRESS] elapsed=12.4s avg_per_folder=3.10s eta=~18.6s"
