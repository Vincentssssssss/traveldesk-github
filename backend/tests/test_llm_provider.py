import unittest

from agents.llm_provider import extract_text_content


class ExtractTextContentTests(unittest.TestCase):
    def test_returns_string_content_directly(self):
        self.assertEqual(extract_text_content("hello"), "hello")

    def test_flattens_responses_content_blocks(self):
        blocks = [
            {"type": "reasoning", "summary": "internal"},
            {"type": "output_text", "text": '{"intent":"general_faq"}'},
        ]
        self.assertEqual(extract_text_content(blocks), '{"intent":"general_faq"}')

    def test_handles_langchain_content_item_objects(self):
        class ContentItem:
            def __init__(self, text: str):
                self.text = text

        blocks = [ContentItem("first"), ContentItem(" second")]
        self.assertEqual(extract_text_content(blocks), "first second")


if __name__ == "__main__":
    unittest.main()
