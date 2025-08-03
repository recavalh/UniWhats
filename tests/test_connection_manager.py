import pytest
from backend.server import ConnectionManager


def test_disconnect_handles_unknown_websocket():
    """Calling disconnect on a websocket that was never connected should not raise an error"""
    manager = ConnectionManager()
    fake_ws = object()
    try:
        manager.disconnect(fake_ws)
    except ValueError:
        pytest.fail("disconnect raised ValueError for unknown websocket")
    assert manager.active_connections == []
