"""
Unit tests for test.py
"""

# pylint: skip-file

import builtins
from unittest.mock import patch

import src.test as test_script


@patch("src.test.AnimalClassifier")
def test_main_runs(mock_classifier):
    """Test that main() runs and prints expected values."""

    mock_instance = mock_classifier.return_value

    mock_instance.predict.return_value = ("Dog", 0.95)

    captured = []

    def fake_print(*args):
        captured.append(" ".join(map(str, args)))

    with patch.object(builtins, "print", fake_print):
        test_script.main("fake_path.jpg")

    mock_instance.predict.assert_called_once_with("fake_path.jpg")

    assert "Class: Dog" in captured[0]
    assert "Confidence:" in captured[1]


def test_main_importable():
    """Test import does not error."""
    import src.test

    assert True
