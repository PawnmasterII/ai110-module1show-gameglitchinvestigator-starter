import os

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from game_engine import (
    GameState,
    CATEGORIES,
    CATEGORY_HINTS,
    MAX_QUESTIONS,
    DIFFICULTIES,
    validate_category,
    validate_question,
    validate_guess,
)
from ai_client import (
    generate_secret_item,
    answer_question,
    evaluate_guess,
    rate_strategy,
    check_answer_consistency,
    get_proximity_feedback,
    test_api_key,
)
from agent_logger import get_agent_logger


st.set_page_config(page_title="AI 20 Questions", page_icon="🤔", layout="wide")

st.title("🤔 AI 20 Questions")
st.caption(
    "An AI-powered evolution of the classic guessing game. "
    "The AI thinks of something — you ask yes/no questions to figure it out!"
)

if "game" not in st.session_state:
    st.session_state.game = GameState()

game = st.session_state.game
agent_logger = get_agent_logger()

with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown(f"**Max Questions:** {MAX_QUESTIONS}")

    difficulty = st.selectbox(
        "Difficulty",
        options=list(DIFFICULTIES.keys()),
        index=1,
        help="Harder difficulties pick more obscure items.",
    )
    show_proximity = st.checkbox(
        "🧭 Proximity Hints",
        value=False,
        help="After each question, the AI tells you if you're getting warmer or colder.",
    )
    show_agent_steps = st.checkbox(
        "🤖 Show Agent Steps",
        value=False,
        help="Show the AI's internal reasoning steps (Plan → Act → Check → Reflect).",
    )

    if game.secret_item and game.status != "setup":
        with st.expander("🔧 Debug Info"):
            st.write(f"Secret: {game.secret_item}")
            st.write(f"Status: {game.status}")
            st.write(f"Questions left: {game.questions_remaining}")
            st.write(f"Guesses: {len(game.guesses)}")
            st.write(f"Difficulty: {difficulty}")

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Required to play. Your key is never stored.",
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    if st.button("🔑 Test API Key", use_container_width=True):
        if not api_key:
            st.error("Enter an API key first.")
        else:
            with st.spinner("Testing..."):
                try:
                    test_api_key()
                    st.success("API key is valid and working!")
                except Exception as e:
                    st.error(f"API key test failed: {e}")

    st.divider()
    if st.button("🔄 New Game", use_container_width=True):
        agent_logger.clear()
        st.session_state.game = GameState()
        st.rerun()

    st.divider()
    st.caption("Built with Streamlit + OpenAI GPT-4o-mini")


if not api_key:
    st.warning("Please enter your OpenAI API key in the sidebar to start playing.")
    st.stop()


if game.status == "setup":
    st.header("🎯 Choose a Category")
    st.markdown("Pick a category and the AI will think of something for you to guess.")

    cols = st.columns(3)
    for i, (cat, desc) in enumerate(CATEGORIES.items()):
        with cols[i % 3]:
            if st.button(f"🏷️ {cat}", key=f"cat_{cat}", use_container_width=True):
                agent_logger.clear()
                with st.spinner("🤖 AI is thinking of something..."):
                    result = generate_secret_item(cat, desc, difficulty)
                    game.setup_game(
                        category=cat,
                        secret_item=result["item"],
                        secret_attributes=result["attributes"],
                    )
                st.rerun()
    st.stop()


progress = game.get_progress_fraction()
st.progress(progress, text=f"Questions used: {MAX_QUESTIONS - game.questions_remaining} / {MAX_QUESTIONS}")

col_info, col_score = st.columns([3, 1])
with col_info:
    st.info(f"📂 Category: **{game.category}**")
with col_score:
    score_display = game.get_score() if game.status == "won" else "—"
    st.metric("Score", score_display)

if game.category in CATEGORY_HINTS:
    with st.expander("💡 Hint: Good questions to ask"):
        st.markdown(CATEGORY_HINTS[game.category])


agent_steps = agent_logger.get_steps_for_display()
if show_agent_steps and agent_steps:
    with st.expander("🤖 Agent Workflow Steps", expanded=True):
        for step in agent_steps:
            phase_emoji = {
                "1. Plan": "📋",
                "2. Act": "⚡",
                "3. Check": "🔍",
                "4. Reflect": "💭",
            }.get(step["phase"], "⚙️")
            st.markdown(
                f"**{phase_emoji} {step['phase']} — {step['step']}**  \n"
                f"`{step['summary']}`"
            )
            if step.get("rationale"):
                st.caption(f"💡 *{step['rationale']}*")


if game.questions_asked:
    st.subheader("📜 Q&A History")
    for i, (q, a) in enumerate(zip(game.questions_asked, game.answers_given), 1):
        hint = game.hints_given[i - 1] if i - 1 < len(game.hints_given) else None
        is_guess = q.startswith("Guess:")
        if is_guess:
            answer_emoji = "✅" if "Correct" in a else "❌"
            st.markdown(
                f"**Q{i}:** {q}  \n"
                f"{answer_emoji} **{a}**"
            )
        else:
            answer_emoji = {"Yes": "✅", "No": "❌", "Sometimes": "🤷"}.get(a, "💬")
            with st.container():
                st.markdown(
                    f"**Q{i}:** {q}  \n"
                    f"{answer_emoji} **{a}**"
                    + (f"  \n💡 *Hint: {hint}*" if hint else "")
                )
    st.divider()


if game.status == "playing":
    tab_question, tab_guess = st.tabs(["❓ Ask a Question", "🎯 Make a Guess"])

    with tab_question:
        with st.form("question_form"):
            question_input = st.text_input(
                "Ask a yes/no question:",
                placeholder="e.g., Is it larger than a car?",
            )
            ask_submitted = st.form_submit_button("Ask 📤", use_container_width=True)

        if ask_submitted:
            ok, err = validate_question(question_input)
            if not ok:
                st.error(err)
            else:
                with st.spinner("🤖 AI is thinking..."):
                    result = answer_question(
                        question=question_input,
                        qa_history=game.get_qa_pairs(),
                        secret_item=game.secret_item,
                        secret_attributes=game.secret_attributes,
                    )

                answer = result.get("answer", "Sometimes")
                hint = result.get("hint", None)
                game.add_qa(question_input, answer, hint)

                if game.is_game_over():
                    st.rerun()
                else:
                    answer_emoji = {"Yes": "✅", "No": "❌", "Sometimes": "🤷"}.get(
                        answer, "💬"
                    )
                    st.markdown(f"{answer_emoji} **Answer: {answer}**")
                    if hint:
                        st.info(f"💡 Hint: {hint}")
                    if show_proximity:
                        try:
                            prox = get_proximity_feedback(
                                question=question_input,
                                qa_history=game.get_qa_pairs(),
                                secret_item=game.secret_item,
                                secret_attributes=game.secret_attributes,
                            )
                            direction = prox.get("direction", "same")
                            proximity = prox.get("proximity", "")
                            feedback = prox.get("feedback", "")
                            dir_emoji = {"warmer": "🔥", "colder": "❄️", "same": "➡️"}.get(direction, "➡️")
                            prox_emoji = {
                                "very close": "🎯",
                                "close": "🔥",
                                "getting there": "🌤️",
                                "far": "🌫️",
                                "very far": "🏔️",
                            }.get(proximity, "")
                            st.markdown(
                                f"{dir_emoji} **Direction:** {direction.title()}  "
                                f"{prox_emoji} **Proximity:** {proximity.title()}"
                            )
                            if feedback:
                                st.caption(f"*{feedback}*")
                        except Exception:
                            pass
                    st.rerun()

    with tab_guess:
        with st.form("guess_form"):
            guess_input = st.text_input(
                "What do you think it is?",
                placeholder="e.g., Is it a penguin?",
            )
            guess_submitted = st.form_submit_button("Guess! 🎯", use_container_width=True)

        if guess_submitted:
            ok, err = validate_guess(guess_input)
            if not ok:
                st.error(err)
            else:
                with st.spinner("🤖 Evaluating your guess..."):
                    result = evaluate_guess(guess_input, game.secret_item)

                correct = result.get("correct", False)
                close = result.get("close", False)
                message = result.get("message", "")
                game.add_guess(guess_input, correct, message)

                if correct:
                    st.balloons()
                    st.success(message)
                    st.markdown(
                        f"🏆 **You got it in {MAX_QUESTIONS - game.questions_remaining} questions!**"
                    )
                else:
                    if close:
                        st.warning(f"🔥 So close! {message}")
                    else:
                        st.error(f"❌ {message}")
                    st.info("Keep asking questions!")


if game.status == "won":
    st.balloons()
    st.success(f"🎉 Congratulations! The answer was **{game.secret_item}**!")
    st.metric("Final Score", game.get_score())

    if st.button("📊 Get Strategy Report", use_container_width=True):
        with st.spinner("🤖 Analyzing your strategy..."):
            report = rate_strategy(
                qa_history=game.get_qa_pairs(),
                secret_item=game.secret_item,
                won=True,
                questions_used=MAX_QUESTIONS - game.questions_remaining,
            )

        st.subheader("📊 Strategy Report")
        st.metric("Rating", f"{report.get('rating', 'N/A')}/10")

        col_s, col_i = st.columns(2)
        with col_s:
            st.markdown("**✅ Strengths:**")
            for s in report.get("strengths", []):
                st.markdown(f"- {s}")
        with col_i:
            st.markdown("**📈 Improvements:**")
            for imp in report.get("improvements", []):
                st.markdown(f"- {imp}")

        if report.get("best_question"):
            st.info(f"🏅 Best question: *{report['best_question']}*")
        if report.get("summary"):
            st.markdown(f"**Summary:** {report['summary']}")

    if st.button("🔍 Check AI Consistency", use_container_width=True):
        with st.spinner("🤖 Running consistency check..."):
            consistency = check_answer_consistency(
                qa_history=game.get_qa_pairs(),
                secret_item=game.secret_item,
                secret_attributes=game.secret_attributes,
            )

        st.subheader("🔍 Consistency Report")
        consistent = consistency.get("consistent", True)
        if consistent:
            st.success("✅ AI was consistent throughout the game!")
        else:
            st.error("❌ AI had some inconsistencies:")
            for c in consistency.get("contradictions", []):
                st.markdown(f"- {c}")

        accuracy = consistency.get("accuracy", 100)
        st.metric("Answer Accuracy", f"{accuracy}%")

        issues = consistency.get("issues", [])
        if issues:
            st.warning("Issues found:")
            for issue in issues:
                st.markdown(f"- {issue}")


if game.status == "lost":
    st.error(f"⏰ Out of questions! The answer was **{game.secret_item}**.")

    with st.expander("📖 About the answer"):
        if game.secret_attributes:
            st.markdown(f"**Description:** {game.secret_attributes.get('description', 'N/A')}")
            for k, v in game.secret_attributes.items():
                if k != "description":
                    st.markdown(f"- **{k.replace('_', ' ').title()}:** {v}")

    if st.button("📊 Get Strategy Report", use_container_width=True):
        with st.spinner("🤖 Analyzing your strategy..."):
            report = rate_strategy(
                qa_history=game.get_qa_pairs(),
                secret_item=game.secret_item,
                won=False,
                questions_used=MAX_QUESTIONS,
            )

        st.subheader("📊 Strategy Report")
        st.metric("Rating", f"{report.get('rating', 'N/A')}/10")

        col_s, col_i = st.columns(2)
        with col_s:
            st.markdown("**✅ Strengths:**")
            for s in report.get("strengths", []):
                st.markdown(f"- {s}")
        with col_i:
            st.markdown("**📈 Improvements:**")
            for imp in report.get("improvements", []):
                st.markdown(f"- {imp}")

        if report.get("summary"):
            st.markdown(f"**Summary:** {report['summary']}")
