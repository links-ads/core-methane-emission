from methane_emission.cli import main
from methane_emission.core import greet


def test_example_fixture(example_fixture):
    assert example_fixture == 1


def test_greet():
    assert greet("world") == "Hello, world!"


def test_cli(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["methane-emission", "world"])
    main()
    captured = capsys.readouterr()
    assert "Hello, world!" in captured.out
