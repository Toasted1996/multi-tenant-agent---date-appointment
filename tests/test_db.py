from unittest.mock import MagicMock, patch


def test_get_db_client_returns_supabase_client():
    with patch("app.db.create_client") as mock_create:
        mock_create.return_value = MagicMock()
        from app.db import get_db_client
        client = get_db_client()
        assert client is not None
        mock_create.assert_called_once()
