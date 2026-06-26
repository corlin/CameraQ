import pytest
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

@pytest.fixture
def sample_image_path():
    # Helper to return a path to a sample image for testing
    return "tests/data/sample.jpg"
