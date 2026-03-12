from dataclasses import dataclass


@dataclass(slots=True)
class Question:
    question: str
    options: list[str]
    correct_answer: str

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        return cls(
            question=str(data["question"]),
            options=[str(option) for option in data["options"]],
            correct_answer=str(data["correct_answer"]),
        )

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "options": list(self.options),
            "correct_answer": self.correct_answer,
        }
