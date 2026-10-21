"""Question-bank initialization must preserve existing interview data."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import init_db, models


class QuestionBankSeedTests(unittest.TestCase):
    def test_questions_only_preserves_existing_data_and_is_repeatable(self):
        engine = create_engine("sqlite:///:memory:")
        models.Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine)
        self.addCleanup(engine.dispose)
        with factory() as db:
            db.add(models.User(
                id="existing-user", email="existing@example.test",
                full_name="Existing user", role="USER", hashed_password="unchanged-hash",
            ))
            db.add(models.InterviewSession(
                id="existing-session", user_id="existing-user",
                role_name="Backend Developer", status="COMPLETED", overall_score=81,
            ))
            db.commit()

        with patch.object(init_db, "engine", engine), patch.object(init_db, "SessionLocal", factory), \
                patch.object(init_db, "get_password_hash") as hash_password, redirect_stdout(io.StringIO()):
            init_db.init_database(questions_only=True)
            with factory() as db:
                self.assertEqual(db.query(models.Position).count(), 9)
                question_count = db.query(models.Question).count()
                self.assertGreater(question_count, 0)
                question = db.query(models.Question).filter_by(position_id="backend").first()
                question_id = question.id
                question.question_text = "Existing edited question must remain"
                db.commit()

            init_db.init_database(questions_only=True)
            hash_password.assert_not_called()
            with factory() as db:
                self.assertEqual(db.query(models.User).count(), 1)
                self.assertEqual(db.get(models.User, "existing-user").hashed_password, "unchanged-hash")
                self.assertEqual(db.query(models.InterviewSession).count(), 1)
                self.assertEqual(db.get(models.InterviewSession, "existing-session").overall_score, 81)
                self.assertEqual(db.query(models.Position).count(), 9)
                self.assertEqual(db.query(models.Question).count(), question_count)
                self.assertEqual(db.get(models.Question, question_id).question_text,
                                 "Existing edited question must remain")


if __name__ == "__main__":
    unittest.main()
