from game_engine import (
    GameState,
    CATEGORIES,
    MAX_QUESTIONS,
    validate_category,
    validate_question,
    validate_guess,
)


class TestGameStateSetup:
    def test_initial_state(self):
        game = GameState()
        assert game.status == "setup"
        assert game.category is None
        assert game.secret_item is None
        assert game.questions_remaining == MAX_QUESTIONS
        assert game.questions_asked == []
        assert game.answers_given == []
        assert game.hints_given == []
        assert game.guesses == []

    def test_setup_game(self):
        game = GameState()
        game.setup_game(
            category="Animal",
            secret_item="Penguin",
            secret_attributes={"description": "A flightless bird"},
        )
        assert game.status == "playing"
        assert game.category == "Animal"
        assert game.secret_item == "Penguin"

    def test_reset(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_qa("Is it furry?", "Yes")
        game.add_guess("Cat", True)
        game.reset()
        assert game.status == "setup"
        assert game.category is None
        assert game.questions_asked == []
        assert game.guesses == []


class TestGameStateQA:
    def test_add_qa(self):
        game = GameState()
        game.setup_game("Animal", "Dog", {})
        game.add_qa("Does it bark?", "Yes", "Think about common pets")
        assert len(game.questions_asked) == 1
        assert game.questions_asked[0] == "Does it bark?"
        assert game.answers_given[0] == "Yes"
        assert game.hints_given[0] == "Think about common pets"
        assert game.questions_remaining == MAX_QUESTIONS - 1

    def test_add_qa_without_hint(self):
        game = GameState()
        game.setup_game("Object", "Toaster", {})
        game.add_qa("Is it electronic?", "Yes")
        assert len(game.hints_given) == 0

    def test_multiple_qa(self):
        game = GameState()
        game.setup_game("Animal", "Elephant", {})
        for i in range(5):
            game.add_qa(f"Question {i}?", "Yes")
        assert len(game.questions_asked) == 5
        assert game.questions_remaining == MAX_QUESTIONS - 5

    def test_get_qa_pairs(self):
        game = GameState()
        game.setup_game("Food", "Pizza", {})
        game.add_qa("Is it Italian?", "Yes")
        game.add_qa("Is it sweet?", "No")
        pairs = game.get_qa_pairs()
        assert len(pairs) == 2
        assert pairs[0] == ("Is it Italian?", "Yes")
        assert pairs[1] == ("Is it sweet?", "No")


class TestGameStateGuessing:
    def test_add_correct_guess(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_guess("Cat", True)
        assert game.status == "won"
        assert game.guesses[0]["correct"] is True

    def test_add_wrong_guess(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_guess("Dog", False)
        assert game.status == "playing"
        assert game.guesses[0]["correct"] is False

    def test_multiple_guesses(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_guess("Dog", False)
        game.add_guess("Bird", False)
        game.add_guess("Cat", True)
        assert len(game.guesses) == 3
        assert game.status == "won"


class TestGameStateGameOver:
    def test_game_over_on_win(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_guess("Cat", True)
        assert game.is_game_over() is True

    def test_game_over_on_no_questions(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        for i in range(MAX_QUESTIONS):
            game.add_qa(f"Q{i}?", "Yes")
        assert game.is_game_over() is True
        assert game.status == "lost"

    def test_not_game_over_while_playing(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_qa("Is it furry?", "Yes")
        assert game.is_game_over() is False

    def test_game_not_over_with_remaining_questions(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        for i in range(MAX_QUESTIONS - 1):
            game.add_qa(f"Q{i}?", "Yes")
        assert game.is_game_over() is False
        assert game.questions_remaining == 1


class TestGameStateScoring:
    def test_score_zero_when_not_won(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        assert game.get_score() == 0

    def test_score_when_won(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_qa("Is it furry?", "Yes")
        game.add_qa("Does it purr?", "Yes")
        game.add_guess("Cat", True)
        score = game.get_score()
        assert score > 0

    def test_score_higher_with_fewer_questions(self):
        game1 = GameState()
        game1.setup_game("Animal", "Cat", {})
        game1.add_guess("Cat", True)

        game2 = GameState()
        game2.setup_game("Animal", "Cat", {})
        for i in range(10):
            game2.add_qa(f"Q{i}?", "Yes")
        game2.add_guess("Cat", True)

        assert game1.get_score() > game2.get_score()


class TestGameStateProgress:
    def test_progress_starts_at_zero(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        assert game.get_progress_fraction() == 0.0

    def test_progress_increases(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_qa("Q1?", "Yes")
        assert game.get_progress_fraction() > 0.0

    def test_progress_full(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        for i in range(MAX_QUESTIONS):
            game.add_qa(f"Q{i}?", "Yes")
        assert game.get_progress_fraction() == 1.0


class TestGameStateSerialization:
    def test_to_dict(self):
        game = GameState()
        game.setup_game("Animal", "Penguin", {"description": "Flightless bird"})
        game.add_qa("Can it fly?", "No")
        d = game.to_dict()
        assert d["category"] == "Animal"
        assert d["secret_item"] == "Penguin"
        assert d["status"] == "playing"
        assert len(d["questions_asked"]) == 1
        assert d["questions_remaining"] == MAX_QUESTIONS - 1

    def test_to_dict_returns_copy(self):
        game = GameState()
        game.setup_game("Animal", "Cat", {})
        game.add_qa("Q?", "Yes")
        d = game.to_dict()
        d["questions_asked"].append("Extra")
        assert len(game.questions_asked) == 1


class TestValidateCategory:
    def test_valid_category(self):
        ok, err = validate_category("Animal")
        assert ok is True
        assert err is None

    def test_invalid_category(self):
        ok, err = validate_category("Pokemon")
        assert ok is False
        assert err is not None

    def test_all_categories_valid(self):
        for cat in CATEGORIES:
            ok, err = validate_category(cat)
            assert ok is True


class TestValidateQuestion:
    def test_valid_question(self):
        ok, err = validate_question("Is it an animal?")
        assert ok is True

    def test_empty_question(self):
        ok, err = validate_question("")
        assert ok is False

    def test_none_question(self):
        ok, err = validate_question(None)
        assert ok is False

    def test_too_short(self):
        ok, err = validate_question("a?")
        assert ok is False

    def test_no_question_mark(self):
        ok, err = validate_question("Is it big")
        assert ok is False


class TestValidateGuess:
    def test_valid_guess(self):
        ok, err = validate_guess("Penguin")
        assert ok is True

    def test_empty_guess(self):
        ok, err = validate_guess("")
        assert ok is False

    def test_none_guess(self):
        ok, err = validate_guess(None)
        assert ok is False

    def test_too_short(self):
        ok, err = validate_guess("a")
        assert ok is False
