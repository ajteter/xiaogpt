import unittest

from xiaogpt.config import Config
from xiaogpt.xiaogpt import MiGPT


class RecallCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = object.__new__(MiGPT)
        self.app.config = Config(bot="llama")
        self.app.pending_query = None
        self.app.previous_record = None

    def test_recall_keyword_matches_with_wakeup_prefix(self) -> None:
        record = {"query": "小爱同学，回答上一句"}

        self.assertTrue(self.app.need_recall_previous_query(record))

    def test_change_prompt_keyword_matches_with_wakeup_prefix(self) -> None:
        record = {"query": "小爱同学，更改提示词请简短回答"}

        self.assertTrue(self.app.need_change_prompt(record))

    def test_start_and_end_conversation_match_with_wakeup_prefix(self) -> None:
        self.assertTrue(self.app._is_start_conversation_query("小爱同学，开始持续对话"))
        self.assertTrue(self.app._is_end_conversation_query("小爱同学，结束持续对话"))


if __name__ == "__main__":
    unittest.main()
