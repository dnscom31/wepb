"""Run with: python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from streamlit.testing.v1 import AppTest
from math_engine import build_day, check
from storage import read_submissions, save_submission


class HomeworkUI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = os.environ.get('HOMEWORK_DB_PATH')
        self.old_pin = os.environ.get('HOMEWORK_ADMIN_PIN')
        os.environ['HOMEWORK_DB_PATH'] = str(Path(self.temp.name) / 'test.db')
        os.environ['HOMEWORK_ADMIN_PIN'] = 'test-only-pin'

    def tearDown(self):
        for key, value in [('HOMEWORK_DB_PATH', self.old_db), ('HOMEWORK_ADMIN_PIN', self.old_pin)]:
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp.cleanup()

    def app(self):
        at = AppTest.from_file(str(APP_DIR / 'streamlit_app.py'), default_timeout=30).run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(len(at.error), 0)
        return at

    def click(self, at, label):
        next(button for button in at.button if button.label == label).click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(len(at.error), 0)

    def test_all_126_original_questions_have_valid_expected_answers(self):
        for day in range(1, 8):
            questions = build_day(day)
            self.assertEqual(len(questions), 18)
            for question in questions:
                self.assertTrue(check(question, str(question['ans']))[0], (day, question))

    def test_blank_name_and_unanswered_submission(self):
        at = self.app()
        self.click(at, '오늘의 18문제 시작')
        self.assertTrue(at.warning)
        at.text_input(key='student_name').set_value('가상학생')
        at.selectbox[0].select(1)
        self.click(at, '오늘의 18문제 시작')
        self.click(at, '전체 답 제출하고 채점하기')
        self.assertTrue(at.warning)
        self.assertTrue(read_submissions().empty)

    def test_group_navigation_retry_and_new_student_reset(self):
        at = self.app()
        at.text_input(key='student_name').set_value('가상학생')
        at.selectbox[0].select(1)
        self.click(at, '오늘의 18문제 시작')
        questions = build_day(1)
        for i in range(6):
            at.text_input[i].set_value(str(questions[i]['ans'] + (1 if i < 2 else 0)))
        self.click(at, '다음 6문항')
        self.click(at, '이전 6문항')
        self.assertEqual(at.text_input[0].value, str(questions[0]['ans'] + 1))
        self.click(at, '다음 6문항')
        for i in range(6, 12):
            at.text_input[i - 6].set_value(str(questions[i]['ans']))
        self.click(at, '다음 6문항')
        for i in range(12, 18):
            at.text_input[i - 12].set_value(str(questions[i]['ans']))
        self.click(at, '전체 답 제출하고 채점하기')
        self.assertEqual(at.session_state['phase'], 'result')
        self.assertEqual(at.session_state['last_grade']['score'], 16)
        self.click(at, '틀린 2문항 다시 풀기')
        self.assertEqual(len(at.text_input), 2)
        for i in range(2):
            at.text_input[i].set_value(str(questions[i]['ans']))
        self.click(at, '오답 제출하고 다시 채점하기')
        self.assertEqual(at.session_state['last_grade']['score'], 18)
        records = read_submissions('가상학생')
        self.assertEqual(records['attempt'].tolist(), [2, 1])
        self.click(at, '학습 과정으로 돌아가기')
        at.text_input(key='student_name').set_value('새학생')
        self.click(at, '오늘의 18문제 시작')
        self.assertIsNone(at.session_state['retry_indices'])
        self.assertTrue(all(not answer for answer in at.session_state['answers']))
        self.assertEqual(len(at.text_input), 6)

    def test_teacher_login_filters_and_rerun_persistence(self):
        save_submission('가상학생A', 1, 16, 18, 120, '분수 사칙연산 2문항')
        save_submission('가상학생B', 1, 18, 18, 120, '없음')
        save_submission('가상학생C', 2, 18, 18, 120, '없음')
        at = self.app()
        at.radio(key='view').set_value('교사 관리').run()
        at.text_input[0].set_value('wrong')
        next(b for b in at.button if b.label == '학생 결과 확인').click().run()
        self.assertTrue(at.error)
        at.text_input[0].set_value('test-only-pin')
        self.click(at, '학생 결과 확인')
        at.selectbox(key='teacher_day').select(1).run()
        self.assertEqual(len(at.dataframe[0].value), 3)
        status = next(s for s in at.selectbox if s.label == '학습 상태')
        status.select('미제출').run()
        self.assertEqual(at.dataframe[0].value['학생'].tolist(), ['가상학생C'])
        self.assertTrue(at.session_state['admin_authenticated'])
        next(s for s in at.selectbox if s.label == '학습 상태').select('전체').run()
        next(t for t in at.text_input if t.label == '학생 검색').set_value('없는학생').run()
        self.assertTrue(any('조건에 맞는 학생' in info.value for info in at.info))
        self.click(at, '교사 화면 로그아웃')
        self.assertFalse(at.session_state['admin_authenticated'])


if __name__ == '__main__':
    unittest.main()
