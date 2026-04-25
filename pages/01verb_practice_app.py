import random
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data.csv"
VERB_LIST_PATH = BASE_DIR / "verb list.csv"
PATTERN_GUIDE_PATH = BASE_DIR / "pattern guide.xlsx"

REQUIRED_COLUMNS = [
    "id",
    "pattern",
    "blank_sentence",
    "korean_sentence",
    "correct_verb",
    "option_b",
    "option_c",
    "option_d",
    "sentence_structure",
    "category",
    "difficulty",
    "feedback_correct",
    "feedback_wrong",
]

st.set_page_config(
    page_title="Verb Practice App",
    page_icon="✅",
    layout="centered",
)


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


@st.cache_data
def load_pattern_guide():
    if not PATTERN_GUIDE_PATH.exists():
        return pd.DataFrame(columns=["pattern_no", "pattern_name", "structure", "example", "key_verbs"])

    guide = pd.read_excel(PATTERN_GUIDE_PATH)
    guide.columns = [normalize_text(c) for c in guide.columns]
    for col in ["pattern_no", "pattern_name", "structure", "example", "key_verbs"]:
        if col not in guide.columns:
            guide[col] = ""
    guide["pattern_no"] = pd.to_numeric(guide["pattern_no"], errors="coerce").astype("Int64")
    return guide


@st.cache_data
def load_verb_list():
    if not VERB_LIST_PATH.exists():
        return pd.DataFrame(columns=["verb", "type", "pattern", "korean_meaning", "example"])

    verbs = pd.read_csv(VERB_LIST_PATH, encoding="utf-8-sig")
    verbs.columns = [normalize_text(c) for c in verbs.columns]
    for col in ["verb", "type", "pattern", "korean_meaning", "example"]:
        if col not in verbs.columns:
            verbs[col] = ""
    return verbs


def apply_manual_corrections(df):
    fixed = df.copy()

    # 원본 17번은 빈칸 정답이 동사가 아니라 out이므로, 동사 선택 문항으로 보정합니다.
    target = fixed["id"].astype(str).str.strip().eq("17")
    if target.any():
        fixed.loc[target, "blank_sentence"] = "The issue ___ out to be more serious than expected."
        fixed.loc[target, "correct_verb"] = "turned"
        fixed.loc[target, "option_b"] = "came"
        fixed.loc[target, "option_c"] = "grew"
        fixed.loc[target, "option_d"] = "got"
        fixed.loc[target, "feedback_correct"] = "Correct! 'turn out to be' = 결국 ~으로 판명되다. 여기서는 동사 turned가 필요합니다."
        fixed.loc[target, "feedback_wrong"] = "정답은 'turned'. turn out to be는 '결국 ~으로 판명되다'라는 표현입니다."

    return fixed


@st.cache_data
def load_question_data():
    if not DATA_PATH.exists():
        st.error("data.csv 파일을 찾을 수 없습니다. 앱 파일과 같은 폴더에 data.csv를 올려주세요.")
        st.stop()

    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    df.columns = [normalize_text(c) for c in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"data.csv에 필요한 열이 없습니다: {', '.join(missing)}")
        st.stop()

    df = apply_manual_corrections(df)

    for col in REQUIRED_COLUMNS:
        df[col] = df[col].apply(normalize_text)

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["pattern"] = pd.to_numeric(df["pattern"], errors="coerce")
    df = df.dropna(subset=["id", "pattern"]).copy()
    df["id"] = df["id"].astype(int)
    df["pattern"] = df["pattern"].astype(int)

    # 정답과 오답 보기를 한 묶음으로 관리합니다.
    # 화면에 보여줄 때는 get_shuffled_options()에서 매번 무작위로 섞습니다.
    df["options"] = df.apply(
        lambda row: [
            row["correct_verb"],
            row["option_b"],
            row["option_c"],
            row["option_d"],
        ],
        axis=1,
    )

    # 빈 보기나 중복 보기가 있으면 퀴즈에서 제외합니다.
    df["is_valid"] = df["options"].apply(lambda opts: len([x for x in opts if x]) == 4 and len(set(opts)) == 4)
    invalid_df = df[~df["is_valid"]].copy()
    valid_df = df[df["is_valid"]].copy()

    return valid_df, invalid_df


def get_pattern_label(pattern_no, guide):
    match = guide[guide["pattern_no"] == pattern_no]
    if match.empty:
        return f"{pattern_no}형식"
    return match.iloc[0]["pattern_name"]


def get_pattern_structure(pattern_no, guide):
    match = guide[guide["pattern_no"] == pattern_no]
    if match.empty:
        return ""
    return match.iloc[0]["structure"]


def reset_quiz_state():
    """새 풀이를 시작할 때 문제 순서와 보기 순서를 모두 새로 섞습니다."""
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.answered = {}
    st.session_state.selected_answers = {}
    st.session_state.shuffled_options_by_qid = {}
    st.session_state.quiz_attempt_id = random.randint(1, 1_000_000_000)
    st.session_state.question_order_seed = random.randint(1, 1_000_000_000)


def initialize_quiz_state():
    if "quiz_attempt_id" not in st.session_state:
        reset_quiz_state()


def get_shuffled_options(question_id, options):
    """
    정답, option_b, option_c, option_d의 위치를 랜덤으로 섞습니다.

    중요:
    Streamlit은 라디오 버튼을 누르거나 정답 확인 버튼을 누를 때마다 화면을 다시 실행합니다.
    그래서 매번 무조건 random.shuffle()을 실행하면, 학생이 고른 직후 보기 순서가 바뀌어
    채점이 꼬일 수 있습니다.

    따라서 한 번 화면에 나온 문제의 보기 순서는 session_state에 저장해 고정하고,
    '처음부터 다시 풀기'를 누르면 새 풀이에서 다시 랜덤 배치되도록 했습니다.
    """
    qid = str(question_id)

    if "shuffled_options_by_qid" not in st.session_state:
        st.session_state.shuffled_options_by_qid = {}

    if qid not in st.session_state.shuffled_options_by_qid:
        shuffled = list(options)
        random.shuffle(shuffled)
        st.session_state.shuffled_options_by_qid[qid] = shuffled

    return st.session_state.shuffled_options_by_qid[qid]


questions, invalid_questions = load_question_data()
pattern_guide = load_pattern_guide()
verb_list = load_verb_list()
initialize_quiz_state()

st.title("Verb Practice App")
st.caption("한글 해석을 먼저 읽고 의미를 파악한 뒤, 영어 문장의 빈칸에 알맞은 동사를 고르세요.")

with st.sidebar:
    st.header("문항 설정")

    pattern_options = ["전체"] + [
        f"{int(row.pattern_no)}형식 - {row.pattern_name}"
        for _, row in pattern_guide.dropna(subset=["pattern_no"]).iterrows()
    ]
    selected_pattern_label = st.selectbox("문장 형식", pattern_options)

    category_options = ["전체"] + sorted(questions["category"].dropna().unique().tolist())
    selected_category = st.selectbox("문장 Category", category_options)

    difficulty_options = ["전체"] + sorted(questions["difficulty"].dropna().unique().tolist())
    selected_difficulty = st.selectbox("난이도", difficulty_options)

    quiz_mode = st.radio("문항 순서", ["섞어서 풀기", "번호순으로 풀기"], horizontal=False)

    if st.button("처음부터 다시 풀기"):
        reset_quiz_state()
        st.rerun()

filtered = questions.copy()

if selected_pattern_label != "전체":
    selected_pattern = int(selected_pattern_label.split("형식")[0])
    filtered = filtered[filtered["pattern"] == selected_pattern]

if selected_category != "전체":
    filtered = filtered[filtered["category"] == selected_category]

if selected_difficulty != "전체":
    filtered = filtered[filtered["difficulty"] == selected_difficulty]

if quiz_mode == "섞어서 풀기":
    filtered = filtered.sample(frac=1, random_state=st.session_state.question_order_seed).reset_index(drop=True)
else:
    filtered = filtered.sort_values("id").reset_index(drop=True)

if filtered.empty:
    st.warning("선택한 조건에 맞는 문항이 없습니다. 왼쪽 설정을 바꿔주세요.")
    st.stop()

if st.session_state.current_index >= len(filtered):
    st.session_state.current_index = 0

current = filtered.iloc[st.session_state.current_index]
qid = int(current["id"])
pattern_label = get_pattern_label(int(current["pattern"]), pattern_guide)
pattern_structure = get_pattern_structure(int(current["pattern"]), pattern_guide)
answered = qid in st.session_state.answered

progress_text = f"{st.session_state.current_index + 1} / {len(filtered)}"
st.progress((st.session_state.current_index + 1) / len(filtered), text=progress_text)

# 상단에 문장 category를 뚜렷하게 표시합니다.
st.markdown(
    f"""
<div style="padding: 0.7rem 1rem; border-radius: 999px; background-color: #eef2ff; border: 1px solid #c7d2fe; display: inline-block; margin-bottom: 0.8rem;">
  <span style="font-size: 0.85rem; color: #4f46e5; font-weight: 700;">문장 Category</span>
  <span style="font-size: 1rem; color: #111827; font-weight: 800; margin-left: 0.5rem;">{current['category']}</span>
</div>
""",
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([2, 1])
with top_left:
    st.markdown(f"### 문제 {qid}")
with top_right:
    st.markdown(f"**현재 점수:** {st.session_state.score}점")

st.markdown(
    f"""
<div style="padding: 1rem; border: 1px solid #e5e7eb; border-radius: 14px; background-color: #fafafa;">
  <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.35rem;">먼저 한글 해석을 읽어보세요.</div>
  <div style="font-size: 1.15rem; font-weight: 700;">{current['korean_sentence']}</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("")

sentence_col, pattern_col = st.columns([3, 1])
with sentence_col:
    st.markdown("#### 영어 문장")
    st.markdown(f"### {current['blank_sentence']}")
with pattern_col:
    st.markdown("#### 문장 형식")
    st.info(pattern_label)

if pattern_structure:
    st.caption(f"기본 구조: {pattern_structure}")

with st.expander("문장 구조 힌트 보기"):
    st.write(current["sentence_structure"])

options = get_shuffled_options(qid, current["options"])
radio_key = f"answer_{st.session_state.quiz_attempt_id}_{qid}_{st.session_state.current_index}"
saved_answer = st.session_state.selected_answers.get(qid)
default_index = options.index(saved_answer) if saved_answer in options else None

selected_answer = st.radio(
    "보기 중 알맞은 동사를 고르세요.",
    options,
    index=default_index,
    key=radio_key,
    disabled=answered,
)

submit_col, nav_col1, nav_col2 = st.columns([2, 1, 1])

with submit_col:
    if st.button("정답 확인", type="primary", disabled=answered):
        if selected_answer is None:
            st.warning("먼저 보기를 하나 선택해 주세요.")
        else:
            st.session_state.selected_answers[qid] = selected_answer
            is_correct = selected_answer == current["correct_verb"]
            st.session_state.answered[qid] = is_correct
            if is_correct:
                st.session_state.score += 1
            st.rerun()

if answered:
    is_correct = st.session_state.answered[qid]
    if is_correct:
        st.success(f"correct feedback: {current['feedback_correct']}")
    else:
        st.error(f"wrong feedback: {current['feedback_wrong']}")
        st.info(f"정답: {current['correct_verb']}")

with nav_col1:
    if st.button("이전 문제", disabled=st.session_state.current_index == 0):
        st.session_state.current_index -= 1
        st.rerun()

with nav_col2:
    if st.button("다음 문제", disabled=st.session_state.current_index >= len(filtered) - 1):
        st.session_state.current_index += 1
        st.rerun()

st.divider()

with st.expander("형식별 핵심 동사 보기"):
    if verb_list.empty:
        st.write("verb list.csv 파일을 찾을 수 없습니다.")
    else:
        selected_pattern_no = int(current["pattern"])
        view = verb_list.copy()
        view["pattern"] = pd.to_numeric(view["pattern"], errors="coerce").astype("Int64")
        view = view[view["pattern"] == selected_pattern_no]
        if view.empty:
            st.write("현재 형식에 해당하는 동사 목록이 없습니다.")
        else:
            st.dataframe(
                view[["verb", "type", "korean_meaning", "example"]],
                hide_index=True,
                use_container_width=True,
            )

with st.expander("데이터 점검 결과"):
    st.write(f"사용 가능한 문항 수: {len(questions)}개")
    if invalid_questions.empty:
        st.write("중복 보기나 빈 보기가 있는 문항은 없습니다.")
    else:
        st.write("아래 문항은 보기 구성이 불완전하여 퀴즈에서 제외되었습니다.")
        st.dataframe(
            invalid_questions[["id", "blank_sentence", "correct_verb", "option_b", "option_c", "option_d"]],
            hide_index=True,
            use_container_width=True,
        )
    st.caption("17번 문항은 원본 데이터에서 빈칸이 동사가 아닌 out이었기 때문에, 앱 안에서 동사 선택 문항으로 자동 보정했습니다.")
