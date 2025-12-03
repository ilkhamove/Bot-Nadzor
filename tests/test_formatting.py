from bot.services.formatting import format_channel_report


def test_format_channel_report_ru():
    data = {
        "title": "Test Channel",
        "username": "testchannel",
        "category": "News",
        "language": "ru",
        "members_count": 1000,
        "avg_post_reach": 500,
        "er": 1.5,
        "created_at": "2023-01-01T12:00:00",
    }
    result = format_channel_report(data, language="ru")
    assert "Test Channel" in result
    assert "@testchannel" in result
    assert "1000" in result
    assert "1.5" in result


def test_format_channel_report_uz():
    data = {
        "name": "Kanal",
        "chat": "kanaluz",
        "avgReach": 42,
        "creation_date": None,
    }
    result = format_channel_report(data, language="uz")
    assert "Kanal" in result
    assert "@kanaluz" in result
    assert "42" in result
