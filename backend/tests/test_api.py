"""Тесты эндпоинтов, но без настоящей базы.

Подменяю get_db_connection на фейковое соединение, чтобы тесты можно было
гонять в CI, где никакого Postgres нет.
"""

import main


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def execute(self, *args, **kwargs):
        return None

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConnection:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, **kwargs):
        return FakeCursor(self._rows)

    def commit(self):
        return None

    def close(self):
        return None


def test_get_pets_returns_instance_and_data(monkeypatch):
    rows = [{"id": 1, "name": "Мурка", "species": "cat", "fullness": 50}]
    monkeypatch.setattr(main, "get_db_connection", lambda: FakeConnection(rows))

    result = main.get_pets()

    assert result["instance"] == main.INSTANCE_ID
    assert result["data"] == rows


def test_feed_pet_returns_404_for_unknown_pet(monkeypatch):
    monkeypatch.setattr(main, "get_db_connection", lambda: FakeConnection([]))

    try:
        main.feed_pet(999)
    except main.HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("Ожидали HTTPException 404")
