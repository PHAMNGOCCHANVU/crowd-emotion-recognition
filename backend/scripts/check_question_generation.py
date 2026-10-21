"""Call the real question generator once, without changing the database or frontend."""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from backend.services.ai_contracts import ServiceError
from backend.services.question_contracts import QuestionGenerationRequest
from backend.services.question_generation_service import generate_interview_questions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True, help="JSON with role_name, level, jd_text, question_count")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    env_path = root / "backend/.env"
    load_dotenv(env_path if env_path.exists() else root / ".env", override=False)
    try:
        request = QuestionGenerationRequest.model_validate_json(args.request.read_text(encoding="utf-8-sig"))
        result = generate_interview_questions(request)
        report = {"input": request.model_dump(mode="json"), "status": "ok", **result,
                  "quality_review": "manual review required for JD relevance and level suitability"}
    except ServiceError as exc:
        report = {"status": "error", "error": {"code": exc.code, "message": str(exc)}}
    except (ValidationError, OSError, ValueError):
        report = {"status": "error", "error": {"code": "invalid_input_or_configuration", "message": "Kiểm tra JSON đầu vào, đường dẫn và cấu hình sinh câu hỏi."}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "metadata": report.get("metadata"),
                      "question_count": len(report.get("questions", [])), "error": report.get("error"),
                      "report": str(args.output)}, ensure_ascii=False))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
