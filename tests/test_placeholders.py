from config import render_message


def test_render_message_replaces_placeholders():
    msg = render_message("Hi {user} from {guild} at {now_iso}", "Guild", "User")
    assert "User" in msg
    assert "Guild" in msg
    assert "now_iso" not in msg
