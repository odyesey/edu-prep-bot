import re

from utils.gettext import _

def validate_answers(answers: str) -> tuple[list, list]:
    answers = answers.split("\n")
    correct_answers = []
    errors = []

    for answer in answers:
        correct_answer = ".".join(answer.split(".")[1:])
        if correct_answer:
            correct_answers.append(correct_answer.strip())
        else:
            errors.append(answer)

    return correct_answers, errors

def keywords_list(keywords: str, lang: str) -> tuple[int, list[str]]:
    errors = []

    keywords = [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]

    pattern = re.compile(r"^[A-Za-z0-9_'-]+$")

    if len(keywords) > 10:
        errors.append(_("resource_keywords_limit", lang))

    if len(set(keywords)) != len(keywords):
        errors.append(_("resource_keywords_duplicate", lang))

    for keyword in keywords:
        if not pattern.fullmatch(keyword):
            errors.append(keyword)

    if errors:
        return 0, errors

    return 1, keywords
