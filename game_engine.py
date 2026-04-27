CATEGORIES = {
    "Animal": "Think of a specific animal (e.g., elephant, penguin, snake, dolphin)",
    "Object": "Think of a common household object (e.g., toaster, umbrella, clock, mirror)",
    "Food": "Think of a specific food item (e.g., pizza, sushi, apple, croissant)",
    "Famous Person": "Think of a well-known person (e.g., Einstein, Beyonce, Shakespeare)",
    "Country": "Think of a country (e.g., Japan, Brazil, Egypt, Australia)",
    "Movie": "Think of a well-known movie (e.g., Titanic, Star Wars, Frozen, Jaws)",
}

CATEGORY_HINTS = {
    "Animal": "Ask about: habitat, size, diet, domestic/wild, number of legs, fur/scales/feathers",
    "Object": "Ask about: location in house, material, function, size, uses electricity",
    "Food": "Ask about: taste (sweet/salty/sour), origin, temperature served, ingredients, meal type",
    "Famous Person": "Ask about: nationality, era, field of work, gender, famous achievements",
    "Country": "Ask about: continent, climate, language, landmarks, population size",
    "Movie": "Ask about: genre, decade, main actor, plot elements, animated or live-action",
}

MAX_QUESTIONS = 20

DIFFICULTIES = {
    "Easy": "very common, everyday items that almost anyone would know (e.g., dog, chair, apple)",
    "Medium": "well-known items that require some thought but are still familiar (e.g., platypus, astrolabe, quinoa)",
    "Hard": "obscure or niche items that most people would struggle to guess (e.g., axolotl, wimmelbuch, durian)",
    "Expert": "extremely obscure, rare, or highly specific items that only experts might know (e.g., tardigrade, antikythera mechanism, caul)",
}


class GameState:
    def __init__(self):
        self.category = None
        self.secret_item = None
        self.secret_attributes = {}
        self.questions_asked = []
        self.answers_given = []
        self.hints_given = []
        self.guesses = []
        self.status = "setup"
        self.questions_remaining = MAX_QUESTIONS

    def reset(self):
        self.category = None
        self.secret_item = None
        self.secret_attributes = {}
        self.questions_asked = []
        self.answers_given = []
        self.hints_given = []
        self.guesses = []
        self.status = "setup"
        self.questions_remaining = MAX_QUESTIONS

    def setup_game(self, category, secret_item, secret_attributes):
        self.category = category
        self.secret_item = secret_item
        self.secret_attributes = secret_attributes
        self.status = "playing"

    def add_qa(self, question, answer, hint=None):
        self.questions_asked.append(question)
        self.answers_given.append(answer)
        if hint:
            self.hints_given.append(hint)
        self.questions_remaining -= 1

    def add_guess(self, guess, correct, result_message=""):
        self.guesses.append({"guess": guess, "correct": correct})
        label = f"Guess: {guess}"
        answer = "Correct!" if correct else f"Incorrect — {result_message}"
        self.questions_asked.append(label)
        self.answers_given.append(answer)
        self.hints_given.append(None)
        self.questions_remaining -= 1
        if correct:
            self.status = "won"
        elif self.questions_remaining <= 0:
            self.status = "lost"

    def is_game_over(self):
        if self.status == "won":
            return True
        if self.questions_remaining <= 0:
            self.status = "lost"
            return True
        return False

    def get_qa_pairs(self):
        return list(zip(self.questions_asked, self.answers_given))

    def to_dict(self):
        return {
            "category": self.category,
            "secret_item": self.secret_item,
            "secret_attributes": self.secret_attributes,
            "questions_asked": list(self.questions_asked),
            "answers_given": list(self.answers_given),
            "hints_given": list(self.hints_given),
            "guesses": list(self.guesses),
            "status": self.status,
            "questions_remaining": self.questions_remaining,
        }

    def get_progress_fraction(self):
        return (MAX_QUESTIONS - self.questions_remaining) / MAX_QUESTIONS

    def get_score(self):
        if self.status != "won":
            return 0
        base = MAX_QUESTIONS - len(self.questions_asked)
        bonus = max(0, 10 - len(self.guesses))
        return base * 10 + bonus * 5


def validate_category(category):
    if category not in CATEGORIES:
        return False, f"Invalid category. Choose from: {', '.join(CATEGORIES.keys())}"
    return True, None


def validate_question(question):
    if not question or not question.strip():
        return False, "Please enter a question."
    if len(question.strip()) < 3:
        return False, "Question is too short."
    if not question.strip().endswith("?"):
        return False, "Questions should end with '?'."
    return True, None


def validate_guess(guess):
    if not guess or not guess.strip():
        return False, "Please enter a guess."
    if len(guess.strip()) < 2:
        return False, "Guess is too short."
    return True, None
