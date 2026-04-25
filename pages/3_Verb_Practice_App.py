import random
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent if APP_DIR.name == "pages" else APP_DIR


def find_data_file(filename: str) -> Path:
    """Find shared data files from the app root, pages folder, or current working directory."""
    candidates = [
        ROOT_DIR / filename,
        APP_DIR / filename,
        Path.cwd() / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    return ROOT_DIR / filename


DATA_PATH = find_data_file("data.csv")
PATTERN_GUIDE_PATH = find_data_file("pattern guide.xlsx")

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

st.markdown(
    """
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 980px;
    }

    .stApp, .stMarkdown, p, span, div, label {
        color: #111111;
    }

    .meta-row {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        align-items: center;
        margin-bottom: 0.8rem;
    }
    .category-pill {
        padding: 0.7rem 1rem;
        border-radius: 999px;
        background-color: #eef2ff;
        border: 1px solid #c7d2fe;
        display: inline-block;
    }
    .pattern-pill {
        padding: 0.7rem 1rem;
        border-radius: 999px;
        background-color: #ecfdf5;
        border: 1px solid #bbf7d0;
        display: inline-block;
    }
    .category-label {
        font-size: 0.85rem;
        color: #4f46e5 !important;
        font-weight: 800;
    }
    .category-value {
        font-size: 1rem;
        color: #111827 !important;
        font-weight: 900;
        margin-left: 0.5rem;
    }

    .question-card {
        min-height: 155px;
        padding: 1.15rem 1.2rem;
        border-radius: 18px;
        background: #ffffff !important;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        color: #111111 !important;
    }
    .korean-card {
        border-left: 8px solid #fb923c;
    }
    .english-card {
        border-left: 8px solid #60a5fa;
    }
    .card-label {
        font-size: 0.98rem;
        color: #374151 !important;
        font-weight: 900;
        margin-bottom: 0.55rem;
    }
    .korean-sentence {
        font-size: 1.18rem;
        line-height: 1.65;
        color: #111111 !important;
        font-weight: 850;
    }
    .english-sentence {
        font-size: 1.28rem;
        line-height: 1.65;
        color: #111111 !important;
        font-weight: 900;
    }

    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
        margin-top: 0.85rem;
        margin-bottom: 1rem;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] p,
    div[data-testid="stExpander"] div {
        color: #111111 !important;
        font-weight: 800;
    }

    .small-muted {
        color: #4b5563 !important;
        font-size: 0.92rem;
    }
    .answer-title {
        color: #111111 !important;
        font-size: 1.18rem;
        font-weight: 900;
        margin-top: 1.1rem;
        margin-bottom: 0.45rem;
    }

    div[data-testid="stRadio"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 18px !important;
        padding: 1rem 1.15rem !important;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
    }
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[role="radiogroup"] label,
    div[role="radiogroup"] label p {
        color: #111111 !important;
        font-size: 1.12rem !important;
        font-weight: 850 !important;
    }
    div[role="radiogroup"] label {
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    }
</style>
""",
    unsafe_allow_html=True,
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


def apply_manual_corrections(df):
    fixed = df.copy()

    # 원본 17번은 빈칸 정답이 동사가 아니라 out이므로, 동사 선택 문항으로 보정합니다.
    if "id" in fixed.columns:
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
        st.error("data.csv 파일을 찾을 수 없습니다.")
        st.info("3페이지 앱에서는 data.csv를 app.py와 같은 가장 바깥 폴더에 두면 됩니다.")
        st.caption(f"현재 찾는 위치: {DATA_PATH}")
        st.stop()

    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    df.columns = [normalize_text(c) for c in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"data.csv에 필요한 열이 없습니다: {', '.join(missing)}")
        st.caption(f"현재 data.csv를 찾은 위치: {DATA_PATH}")
        st.stop()

    df = apply_manual_corrections(df)

    for col in REQUIRED_COLUMNS:
        df[col] = df[col].apply(normalize_text)

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["pattern"] = pd.to_numeric(df["pattern"], errors="coerce")
    df = df.dropna(subset=["id", "pattern"]).copy()
    df["id"] = df["id"].astype(int)
    df["pattern"] = df["pattern"].astype(int)

    df["options"] = df.apply(
        lambda row: [
            row["correct_verb"],
            row["option_b"],
            row["option_c"],
            row["option_d"],
        ],
        axis=1,
    )

    df["is_valid"] = df["options"].apply(
        lambda opts: len([x for x in opts if x]) == 4 and len(set(opts)) == 4
    )
    valid_df = df[df["is_valid"]].copy()
    return valid_df


def get_pattern_label(pattern_no, guide):
    match = guide[guide["pattern_no"] == pattern_no]
    if match.empty:
        return f"{pattern_no}형식"
    return match.iloc[0]["pattern_name"] or f"{pattern_no}형식"


def get_pattern_structure(pattern_no, guide):
    match = guide[guide["pattern_no"] == pattern_no]
    if match.empty:
        return ""
    return normalize_text(match.iloc[0]["structure"])


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
    한 번 화면에 나온 문제의 보기 순서는 session_state에 저장해 고정합니다.
    """
    qid = str(question_id)

    if "shuffled_options_by_qid" not in st.session_state:
        st.session_state.shuffled_options_by_qid = {}

    if qid not in st.session_state.shuffled_options_by_qid:
        shuffled = list(options)
        random.shuffle(shuffled)
        st.session_state.shuffled_options_by_qid[qid] = shuffled

    return st.session_state.shuffled_options_by_qid[qid]


questions = load_question_data()
pattern_guide = load_pattern_guide()
initialize_quiz_state()

st.title("Verb Practice App")
st.caption("한글 해석과 영어 문장을 함께 보며, 빈칸에 알맞은 동사를 고르세요.")

with st.sidebar:
    st.header("문항 설정")

    # pattern guide.xlsx를 못 읽는 상황에서도 data.csv의 pattern 열을 기준으로
    # 1~5형식 선택지가 반드시 뜨도록 만듭니다.
    available_patterns = sorted(questions["pattern"].dropna().astype(int).unique().tolist())

    pattern_name_map = {}
    if not pattern_guide.empty and "pattern_no" in pattern_guide.columns and "pattern_name" in pattern_guide.columns:
        for _, row in pattern_guide.dropna(subset=["pattern_no"]).iterrows():
            try:
                pattern_no = int(row["pattern_no"])
                pattern_name = normalize_text(row["pattern_name"])
                pattern_name_map[pattern_no] = pattern_name
            except Exception:
                pass

    pattern_options = ["전체"]
    for pattern_no in available_patterns:
        pattern_name = pattern_name_map.get(pattern_no, "")
        if pattern_name:
            pattern_options.append(f"{pattern_no}형식 - {pattern_name}")
        else:
            pattern_options.append(f"{pattern_no}형식")

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
    selected_pattern = int(selected_pattern_label.split("형식")[0].strip())
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
display_number = st.session_state.current_index + 1
pattern_label = get_pattern_label(int(current["pattern"]), pattern_guide)
answered = qid in st.session_state.answered

progress_text = f"{display_number} / {len(filtered)}"
st.progress(display_number / len(filtered), text=progress_text)

st.markdown(
    f"""
<div class="meta-row">
  <div class="category-pill">
    <span class="category-label">문장 Category</span>
    <span class="category-value">{escape(str(current['category']))}</span>
  </div>
  <div class="pattern-pill">
    <span class="category-label">Pattern</span>
    <span class="category-value">{escape(str(pattern_label))}</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([2, 1])
with top_left:
    st.markdown(f"### 문제 {display_number}")
with top_right:
    st.markdown(f"**현재 점수:** {st.session_state.score}점")

info_left, info_right = st.columns([1, 1])
with info_left:
    st.markdown(
        f"""
<div class="question-card korean-card">
  <div class="card-label">먼저 한글 뜻을 확인하세요</div>
  <div class="korean-sentence">{escape(str(current['korean_sentence']))}</div>
</div>
""",
        unsafe_allow_html=True,
    )
with info_right:
    st.markdown(
        f"""
<div class="question-card english-card">
  <div class="card-label">영어 문장</div>
  <div class="english-sentence">{escape(str(current['blank_sentence']))}</div>
</div>
""",
        unsafe_allow_html=True,
    )

with st.expander("Hint 🔑"):
    st.write(current["sentence_structure"])

options = get_shuffled_options(qid, current["options"])
radio_key = f"answer_{st.session_state.quiz_attempt_id}_{qid}_{st.session_state.current_index}"
saved_answer = st.session_state.selected_answers.get(qid)
default_index = options.index(saved_answer) if saved_answer in options else None

st.markdown('<div class="answer-title">보기 중 알맞은 동사를 고르세요.</div>', unsafe_allow_html=True)

selected_answer = st.radio(
    "보기 중 알맞은 동사를 고르세요.",
    options,
    index=default_index,
    key=radio_key,
    disabled=answered,
    label_visibility="collapsed",
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
