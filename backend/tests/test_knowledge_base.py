import unittest
from unittest.mock import patch

from tools.knowledge_base import search_faqs, search_policies


class KnowledgeBaseChineseSearchTests(unittest.TestCase):
    @patch("tools.knowledge_base._load_json")
    def test_search_faqs_supports_chinese_keywords(self, mock_load_json):
        mock_load_json.return_value = {
            "faqs": [
                {
                    "id": "FAQ-ZH-001",
                    "question": "How to submit reimbursement?",
                    "answer": "Submit via portal.",
                    "question_zh": "如何提交差旅报销？",
                    "answer_zh": "请通过系统提交并上传发票。",
                    "keywords": ["reimbursement"],
                    "keywords_zh": ["报销", "差旅报销"],
                }
            ]
        }

        results = search_faqs("我想咨询差旅报销流程")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "FAQ-ZH-001")

    @patch("tools.knowledge_base._load_json")
    def test_search_policies_supports_chinese_fields(self, mock_load_json):
        mock_load_json.return_value = {
            "policies": [
                {
                    "id": "POL-ZH-001",
                    "category": "expense",
                    "title": "Expense Policy",
                    "description": "Expense claims must be submitted within 30 days.",
                    "title_zh": "差旅报销政策",
                    "description_zh": "差旅报销需在30天内提交。",
                    "keywords": ["expense"],
                    "keywords_zh": ["报销", "费用"],
                }
            ]
        }

        results = search_policies("报销政策是什么", category="expense")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "POL-ZH-001")


if __name__ == "__main__":
    unittest.main()
