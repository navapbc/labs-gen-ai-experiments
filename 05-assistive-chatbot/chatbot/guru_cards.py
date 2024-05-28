#!/usr/bin/env python
import json
import os

from bs4 import BeautifulSoup


class GuruCardsProcessor:
    def __init__(
        self,
        file_path="./guru_cards_for_nava.json",
        question_key="preferredPhrase",
        content_key="content",
    ):
        self.file_path = file_path
        self.question_key = question_key
        self.content_key = content_key

    def extract_qa_text_from_guru(self):
        json_data = self.cards_as_json()
        question_answers = self._extract_question_answers(json_data)
        return question_answers

    def cards_as_json(self):
        with open(self.file_path, encoding="utf-8") as data_file:
            return json.load(data_file)

    def _extract_question_answers(self, json_data):
        question_answers = {}
        for content in json_data:
            if not content[self.question_key].strip().endswith("?"):
                continue
            soup = BeautifulSoup(content[self.content_key], "html.parser")
            answer = soup.get_text(separator="\n", strip=True)
            question_answers[content[self.question_key].strip()] = answer
        return question_answers


def save_simplified_json(gc_processor):
    "Saves a simplified version of the Guru cards JSON file for easier review"
    json_data = gc_processor.cards_as_json()
    name, ext = os.path.splitext(gc_processor.file_path)
    with open(f"{name}_simplified{ext}", "w", encoding="utf-8") as f:
        simplified_json = []
        for card in json_data:
            tags = [tagsItem.get("value") for tagsItem in card.get("tags", [])]
            boards = [boardsItem.get("title") for boardsItem in card.get("boards", [])]
            soup = BeautifulSoup(card[gc_processor.content_key], "html.parser")
            content = soup.get_text(separator="\n", strip=True)
            simplified_json.append(
                {
                    "preferredPhrase": card["preferredPhrase"],
                    "tags": ",".join(tags),
                    "boards": ",".join(boards),
                    gc_processor.content_key: content,
                }
            )
        json.dump(simplified_json, f, indent=4)


if __name__ == "__main__":
    import sys

    if args := sys.argv[1:]:
        _gc_processor = GuruCardsProcessor(file_path=args[0])
    else:
        _gc_processor = GuruCardsProcessor()

    save_simplified_json(_gc_processor)
