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

    # Mock classifier instance
    mock_instance = mock_classifier.return_value

    # test.py expects (class_name, confidence)
    mock_instance.predict.return_value = ("Dog", 0.95)

    # Capture printed output
    captured = []

    def fake_print(*args):
        captured.append(" ".join(map(str, args)))

    # Patch print
    with patch.object(builtins, "print", fake_print):
        test_script.main("fake_path.jpg")

    # Ensure predict was called properly
    mock_instance.predict.assert_called_once_with("fake_path.jpg")

    # Validate printed output
    assert "Class: Dog" in captured[0]
    assert "Confidence:" in captured[1]


def test_main_importable():
    """Test import does not error."""
    import src.test

    assert True
