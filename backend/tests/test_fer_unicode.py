"""Real OpenCV cascade loading must work under Vietnamese Windows paths."""

from pathlib import Path

import pytest

cv = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from backend.services.fer_service import _load_face_cascade


def test_face_detector_loads_from_unicode_directory(tmp_path, monkeypatch):
    xml = (Path(cv.data.haarcascades) / "haarcascade_frontalface_default.xml").read_text(encoding="utf-8")
    cascade_dir = tmp_path / "thư mục tiếng Việt"
    cascade_dir.mkdir()
    (cascade_dir / "haarcascade_frontalface_default.xml").write_text(xml, encoding="utf-8")
    monkeypatch.setattr(cv.data, "haarcascades", str(cascade_dir))

    detector = _load_face_cascade()
    assert not detector.empty()
    # The regression was an assertion crash here, even with no visible faces.
    faces = detector.detectMultiScale(np.zeros((240, 320), dtype=np.uint8), minSize=(60, 60))
    assert len(faces) == 0


def test_missing_cascade_reports_loading_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(cv.data, "haarcascades", str(tmp_path))
    with pytest.raises(RuntimeError, match="Không thể nạp file Haar Cascade"):
        _load_face_cascade()


def test_invalid_cascade_is_rejected_before_detection(tmp_path, monkeypatch):
    xml = '<?xml version="1.0"?><opencv_storage><invalid>0</invalid></opencv_storage>'
    (tmp_path / "haarcascade_frontalface_default.xml").write_text(xml, encoding="utf-8")
    monkeypatch.setattr(cv.data, "haarcascades", str(tmp_path))
    with pytest.raises(RuntimeError, match="Haar Cascade"):
        _load_face_cascade()
