#!/usr/bin/env python
import json
import os
from functools import cached_property

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
        question_answers = self._extract_question_answers()
        return question_answers

    @cached_property
    def cards_as_json(self):
        with open(self.file_path, encoding="utf-8") as data_file:
            return json.load(data_file)

    def _extract_question_answers(self):
        question_answers = {}
        for content in self.cards_as_json:
            if not content[self.question_key].strip().endswith("?"):
                continue
            soup = BeautifulSoup(content[self.content_key], "html.parser")
            answer = soup.get_text(separator="\n", strip=True)
            question_answers[content[self.question_key].strip()] = answer
        return question_answers


def save_simplified_json(gc_processor):
    "Saves a simplified version of the Guru cards JSON file for easier review"
    name, ext = os.path.splitext(gc_processor.file_path)
    with open(f"{name}_simplified{ext}", "w", encoding="utf-8") as f:
        simplified_json = []
        for card in gc_processor.cards_as_json:
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


def diff_guru_cards(gc_processor1, gc_processor2):
    "Return the differences between two Guru cards JSON files"
    qa1 = gc_processor1.extract_qa_text_from_guru()
    print(f"Number of questions in file 1: {len(qa1)}")
    qa2 = gc_processor2.extract_qa_text_from_guru()
    print(f"Number of questions in file 2: {len(qa2)}")

    q_matches = set(qa1.keys()) & set(qa2.keys())
    print(f"Number of questions in both files: {len(q_matches)}")

    a_matches = set(qa1.values()) & set(qa2.values())
    print(f"Number of answers in both files: {len(a_matches)}")

    diff = {}
    for question, answer in qa1.items():
        if question not in qa2:
            diff[question] = (answer, None)
            continue
        if qa2.get(question) != answer:
            diff[question] = (answer, qa2.get(question))
        qa2.pop(question)
    print(f"Stage 1: number of differences: {len(diff)}")
    print("  Count of answers not in file 2", len([a2 for a1, a2 in diff.values() if a2 is None]))
    print(set([a2 for a1, a2 in diff.values()]))
    # print("\n".join(diff.keys()))
    with open("diff-in1.txt", "w") as f:
        f.write("\n".join(diff.keys()))

    diff2 = {}
    for question, answer in qa2.items():
        if question not in qa1:
            diff2[question] = (None, answer)

    print(f"Stage 2: Number of differences: {len(diff2)}")
    print("  Count of answers not in file 1", len([a1 for a1, a2 in diff2.values() if a1 is None]))
    # print(set([a1 for a1,a2 in diff2.values()]))

    diff |= diff2
    print(f"Final: Number of differences: {len(diff)}")
    return diff


if __name__ == "__main__":
    import sys

    if args := sys.argv[1:]:
        _gc_processor = GuruCardsProcessor(file_path=args[0])
    else:
        _gc_processor = GuruCardsProcessor()

    if len(args) <= 1:
        save_simplified_json(_gc_processor)
    elif len(args) == 2:
        _gc_processor2 = GuruCardsProcessor(file_path=args[1])
        diffs = diff_guru_cards(_gc_processor, _gc_processor2).keys()
        # print("\n".join(diffs))
    elif len(args) == 3:
        if args[1] == "subset":
            with open(args[2], "r", encoding="UTF-8") as subset_file:
                questions_subset = [line.strip() for line in subset_file]

            json_data = _gc_processor.cards_as_json
            # qa = _gc_processor.extract_qa_text_from_guru()

            data_subset = []
            for json_entry in json_data:
                question = json_entry[_gc_processor.question_key].strip()
                if question in questions_subset:
                    questions_subset.remove(question)
                    data_subset.append(json_entry)

            with open("qa_subset.json", "w", encoding="UTF-8") as output_file:
                output_file.write(json.dumps(data_subset, indent=2))

            print("Remaining questions not found:")
            print("\n".join(questions_subset))
    else:
        print("Usage: guru_cards.py [file_path] [file_path2]")
