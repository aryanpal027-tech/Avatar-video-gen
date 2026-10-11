from avatar_video_gen.captions import _fmt_srt_time


def test_fmt_srt_time():
    assert _fmt_srt_time(0.0) == "00:00:00,000"
    assert _fmt_srt_time(61.234) == "00:01:01,234"
