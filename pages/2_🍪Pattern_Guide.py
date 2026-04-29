import html
import random
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pattern Guide", page_icon="🧩", layout="wide")


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    candidates = [current, current.parent]
    for folder in candidates:
        if (folder / "pattern guide.xlsx").exists() or (folder / "pattern guide.csv").exists():
            return folder
    return current


BASE_DIR = find_project_root()
PATTERN_XLSX = BASE_DIR / "pattern guide.xlsx"
PATTERN_CSV = BASE_DIR / "pattern guide.csv"
DATA_CSV = BASE_DIR / "data.csv"
VERB_CSV = BASE_DIR / "verb list.csv"

PATTERN_COLORS = {
    1: {"bg": "#EAF4FF", "deep": "#2F80ED", "soft": "#D8ECFF"},
    2: {"bg": "#EFFFF6", "deep": "#27AE60", "soft": "#DDF8EA"},
    3: {"bg": "#FFF4E6", "deep": "#F2994A", "soft": "#FFE4C2"},
    4: {"bg": "#F5EEFF", "deep": "#9B51E0", "soft": "#EAD9FF"},
    5: {"bg": "#FFF0F6", "deep": "#EB5757", "soft": "#FFDCE7"},
}

PATTERN_KOREAN_EXPLANATIONS = {
    1: "주어와 동사만으로 핵심 의미가 완성되는 문장입니다. 뒤에 장소, 시간, 방법 같은 말이 붙어도 목적어는 아닙니다.",
    2: "주어가 어떤 상태이거나 무엇이 되는지를 설명하는 문장입니다. 동사 뒤의 말은 주어를 설명하는 보어입니다.",
    3: "동사의 행동이 목적어에게 직접 닿는 문장입니다. '무엇을/누구를'에 해당하는 말이 필요합니다.",
    4: "누군가에게 무엇을 주거나 말하거나 보내는 문장입니다. 간접목적어와 직접목적어가 함께 나옵니다.",
    5: "목적어 뒤에 그 목적어의 상태나 역할을 설명하는 말이 더 붙는 문장입니다.",
}

PATTERN_QUESTIONS = {
    1: "누가/무엇이 + 어떻게 되다/움직이다?",
    2: "누가/무엇이 + 어떤 상태이다/되다?",
    3: "누가/무엇을 + 하다?",
    4: "누가 + 누구에게 + 무엇을 + 주다/말하다?",
    5: "누가 + 누구/무엇을 + 어떤 상태로 만들다/부르다/여기다?",
}

STRUCTURE_MEANINGS = {
    "S": "Subject: 주어",
    "V": "Verb: 동사",
    "O": "Object: 목적어",
    "SC": "Subject Complement: 주격보어",
    "IO": "Indirect Object: 간접목적어",
    "DO": "Direct Object: 직접목적어",
    "OC": "Object Complement: 목적격보어",
}

QUIZ_ITEMS = [
    {"question": "She smiled brightly.", "answer": 1, "hint": "동사 smiled 뒤에 꼭 필요한 목적어나 보어가 없습니다."},
    {"question": "The soup smells delicious.", "answer": 2, "hint": "delicious는 주어 The soup의 상태를 설명합니다."},
    {"question": "I finished my homework.", "answer": 3, "hint": "my homework는 '무엇을?'에 대한 목적어입니다."},
    {"question": "He gave me a pencil.", "answer": 4, "hint": "me와 a pencil, 목적어가 두 개 나옵니다."},
    {"question": "The news made her happy.", "answer": 5, "hint": "happy는 목적어 her의 상태를 설명합니다."},
    {"question": "The baby cried.", "answer": 1, "hint": "주어와 동사만으로 의미가 완성됩니다."},
    {"question": "My brother became a teacher.", "answer": 2, "hint": "a teacher는 주어 My brother를 설명합니다."},
    {"question": "They built a small house.", "answer": 3, "hint": "a small house는 built의 목적어입니다."},
    {"question": "Mom told us a story.", "answer": 4, "hint": "us에게 a story를 말해준 구조입니다."},
    {"question": "We call him Joon.", "answer": 5, "hint": "Joon은 목적어 him을 설명하는 말입니다."},
]

st.markdown(
    """
    <style>
    .main-title {font-size: 2.4rem;font-weight: 900;color: inherit;margin-bottom: 0.2rem;}
    .sub-title {font-size: 1.05rem;opacity: 0.82;margin-bottom: 1.3rem;}
    .pattern-card {border-radius: 22px;padding: 22px 24px;margin: 14px 0px;border: 2px solid rgba(0,0,0,0.04);box-shadow: 0 8px 24px rgba(0,0,0,0.06);color: #111111 !important;}
    .pattern-label {display: inline-block;padding: 7px 13px;border-radius: 999px;color: white !important;font-size: 0.95rem;font-weight: 800;margin-bottom: 8px;}
    .structure-box {display: inline-block;padding: 12px 18px;border-radius: 16px;background: rgba(255,255,255,0.88);font-size: 1.45rem;font-weight: 900;letter-spacing: 0.5px;margin: 8px 0px 12px 0px;border: 1px solid rgba(0,0,0,0.06);}
    .guide-text {font-size: 1.08rem;line-height: 1.65;color: #222222 !important;}
    .example-text {font-size: 1.12rem;font-weight: 800;color: #111111 !important;margin-top: 8px;}
    .chip {display: inline-block;padding: 6px 10px;margin: 3px 4px 3px 0px;border-radius: 999px;font-weight: 700;font-size: 0.92rem;background: white;border: 1px solid rgba(0,0,0,0.08);color: #111111 !important;}
    .summary-box {border-radius: 18px;padding: 15px 18px;background: #FFFFFF;border: 1px solid #EAEAF0;margin: 8px 0px;color: #111111 !important;}
    .small-caption {font-size: 0.92rem;color: #555555 !important;}
    .quiz-card {background:#FFFFFF;border:1px solid #E4E7EC;border-radius:20px;padding:20px 22px;margin:12px 0;color:#111111 !important;box-shadow:0 5px 18px rgba(16,24,40,0.06);}
    .quiz-sentence {font-size:1.35rem;font-weight:900;color:#111111 !important;margin-bottom:10px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_pattern_guide() -> pd.DataFrame:
    if PATTERN_XLSX.exists():
        df = pd.read_excel(PATTERN_XLSX, sheet_name="pattern_guide")
    elif PATTERN_CSV.exists():
        df = pd.read_csv(PATTERN_CSV)
    else:
        st.error("pattern guide.xlsx 또는 pattern guide.csv 파일을 찾을 수 없습니다.")
        st.stop()
    required = ["pattern_no", "pattern_name", "structure", "example", "key_verbs"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Pattern guide 파일에 필요한 열이 없습니다: {missing}")
        st.stop()
    df = df.copy()
    df["pattern_no"] = pd.to_numeric(df["pattern_no"], errors="coerce")
    df = df.dropna(subset=["pattern_no"]).sort_values("pattern_no")
    df["pattern_no"] = df["pattern_no"].astype(int)
    return df


@st.cache_data
def load_practice_data() -> pd.DataFrame:
    if not DATA_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(DATA_CSV)
    if "pattern" in df.columns:
        df["pattern"] = pd.to_numeric(df["pattern"], errors="coerce")
    return df


@st.cache_data
def load_verb_list() -> pd.DataFrame:
    if not VERB_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(VERB_CSV)
    if "pattern" in df.columns:
        df["pattern"] = pd.to_numeric(df["pattern"], errors="coerce")
    return df


def esc(value) -> str:
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def get_color(pattern_no: int) -> dict:
    try:
        pattern_no = int(pattern_no)
    except Exception:
        pattern_no = 0
    return PATTERN_COLORS.get(pattern_no, {"bg": "#F7F7F7", "deep": "#555555", "soft": "#EEEEEE"})


def split_key_verbs(text: str) -> list[str]:
    if pd.isna(text):
        return []
    return [item.strip() for item in str(text).split(",") if item.strip()]


def chips(items: list[str], pattern_no: int, limit: int = 14) -> str:
    color = get_color(pattern_no)["soft"]
    shown = items[:limit]
    extra = len(items) - len(shown)
    html_chips = "".join(f'<span class="chip" style="background:{color};">{esc(item)}</span>' for item in shown)
    if extra > 0:
        html_chips += f'<span class="chip">+{extra} more</span>'
    return html_chips


def make_overview_df(df: pd.DataFrame) -> pd.DataFrame:
    overview = df[["pattern_no", "pattern_name", "structure", "example"]].copy()
    overview["pattern_no"] = overview["pattern_no"].apply(lambda x: f"{int(x)}형식")
    return overview.rename(columns={"pattern_no": "형식", "pattern_name": "이름", "structure": "구조", "example": "예문"})


def style_overview_table(df: pd.DataFrame):
    def row_style(row):
        try:
            p = int(str(row["형식"]).replace("형식", ""))
        except Exception:
            p = 0
        color = get_color(p)
        return [f"background-color: {color['bg']}; color: #111111; font-weight: 700; font-size: 16px;" for _ in row]

    return (
        df.style.apply(row_style, axis=1)
        .set_properties(**{"color": "#111111", "border": "1px solid #E4E7EC", "font-size": "16px", "text-align": "left"})
        .set_table_styles([
            {"selector": "th", "props": [("background-color", "#F2F4F7"), ("color", "#111111"), ("font-weight", "900"), ("font-size", "16px"), ("text-align", "left"), ("border", "1px solid #E4E7EC")]},
            {"selector": "td", "props": [("color", "#111111"), ("border", "1px solid #E4E7EC")]},
        ])
    )


def structure_legend() -> str:
    return "".join([f"<span class='chip'>{esc(k)} = {esc(v)}</span>" for k, v in STRUCTURE_MEANINGS.items()])


def render_learning_tab(pattern_df: pd.DataFrame, practice_df: pd.DataFrame, verb_df: pd.DataFrame) -> None:
    st.markdown("### 1. 전체 구조 한눈에 보기")
    overview_df = make_overview_df(pattern_df)
    try:
        st.dataframe(style_overview_table(overview_df), use_container_width=True, hide_index=True, height=255)
    except Exception:
        st.dataframe(overview_df, use_container_width=True, hide_index=True, height=255)

    with st.expander("문장 구조 기호 뜻 보기", expanded=False):
        st.markdown(structure_legend(), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 2. 형식별로 자세히 배우기")
    pattern_options = ["전체"] + [f"{int(row.pattern_no)}형식 - {row.pattern_name}" for row in pattern_df.itertuples()]
    selected = st.selectbox("보고 싶은 형식을 선택하세요.", pattern_options)
    selected_df = pattern_df.copy() if selected == "전체" else pattern_df[pattern_df["pattern_no"] == int(selected.split("형식")[0])]

    for _, row in selected_df.iterrows():
        p = int(row["pattern_no"])
        color = get_color(p)
        key_verbs = split_key_verbs(row["key_verbs"])
        st.markdown(
            f"""
            <div class="pattern-card" style="background:{color['bg']};">
                <span class="pattern-label" style="background:{color['deep']};">{esc(row['pattern_name'])}</span><br>
                <div class="structure-box" style="color:{color['deep']};">{esc(row['structure'])}</div>
                <div class="guide-text"><b>핵심 질문:</b> {esc(PATTERN_QUESTIONS.get(p, '문장 구조를 확인해 보세요.'))}</div>
                <div class="guide-text"><b>이해하기:</b> {esc(PATTERN_KOREAN_EXPLANATIONS.get(p, ''))}</div>
                <div class="example-text">예문: {esc(row['example'])}</div>
                <div class="small-caption">대표 동사</div>
                <div>{chips(key_verbs, p)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ex_col, verb_col = st.columns([1.2, 1])
        with ex_col:
            if not practice_df.empty and "pattern" in practice_df.columns:
                examples = practice_df[practice_df["pattern"] == p].head(4)
                if not examples.empty:
                    st.markdown(f"**{p}형식 연습 문장 예시**")
                    for _, ex in examples.iterrows():
                        st.markdown(
                            f"""
                            <div class="summary-box">
                                <b>한글:</b> {esc(ex.get('korean_sentence', ''))}<br>
                                <b>영어:</b> {esc(ex.get('blank_sentence', ''))}<br>
                                <b>핵심 동사:</b> <span style="color:{color['deep']}; font-weight:900;">{esc(ex.get('correct_verb', ''))}</span><br>
                                <span class="small-caption">{esc(ex.get('sentence_structure', ''))}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
        with verb_col:
            if not verb_df.empty and "pattern" in verb_df.columns:
                verbs = verb_df[verb_df["pattern"] == p].copy()
                if not verbs.empty:
                    st.markdown(f"**{p}형식 동사 목록**")
                    for _, verb_row in verbs.head(8).iterrows():
                        verb = verb_row.get("verb", "")
                        meaning = verb_row.get("korean_meaning", "")
                        st.markdown(f"<span class='chip' style='background:{color['soft']};'><b>{esc(verb)}</b> · {esc(meaning)}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 3. 문장 예시 표로 복습하기")
    if practice_df.empty:
        st.info("data.csv가 있으면 형식별 예문 표가 함께 표시됩니다.")
    else:
        category_values = sorted([str(x) for x in practice_df.get("category", pd.Series(dtype=str)).dropna().unique()])
        pattern_values = sorted([int(x) for x in practice_df["pattern"].dropna().unique()]) if "pattern" in practice_df.columns else []
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_patterns = st.multiselect("표에 보여줄 형식", options=pattern_values, default=pattern_values, format_func=lambda x: f"{x}형식")
        with filter_col2:
            selected_categories = st.multiselect("표에 보여줄 Category", options=category_values, default=category_values)
        view_df = practice_df.copy()
        if selected_patterns:
            view_df = view_df[view_df["pattern"].isin(selected_patterns)]
        if selected_categories and "category" in view_df.columns:
            view_df = view_df[view_df["category"].astype(str).isin(selected_categories)]
        show_cols = [col for col in ["pattern", "category", "korean_sentence", "blank_sentence", "correct_verb", "sentence_structure"] if col in view_df.columns]
        display_df = view_df[show_cols].copy().rename(columns={"pattern": "형식", "category": "Category", "korean_sentence": "한글 의미", "blank_sentence": "영어 문장", "correct_verb": "핵심 동사", "sentence_structure": "문장 구조"})

        def row_style(row):
            p = int(row.get("형식", 0)) if pd.notna(row.get("형식", None)) else 0
            bg = get_color(p)["bg"]
            return [f"background-color: {bg}; color: #111111;" for _ in row]
        try:
            styled_display = display_df.style.apply(row_style, axis=1).set_properties(**{"color": "#111111", "font-size": "15px", "text-align": "left"}).set_table_styles([
                {"selector": "th", "props": [("background-color", "#F2F4F7"), ("color", "#111111"), ("font-weight", "900"), ("text-align", "left")]},
                {"selector": "td", "props": [("color", "#111111")]},
            ])
            st.dataframe(styled_display, use_container_width=True, hide_index=True)
        except Exception:
            st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_quiz_tab(pattern_df: pd.DataFrame) -> None:
    st.markdown("### 📝 Pattern Check Quiz")
    st.caption("문장을 보고 몇 형식인지 고르는 간단한 선택형 문제입니다. 중학생들이 구조를 확인하는 연습용입니다.")

    if "pattern_quiz_choices" not in st.session_state:
        choices = {}
        options = [1, 2, 3, 4, 5]
        for i, item in enumerate(QUIZ_ITEMS):
            shuffled = options.copy()
            random.shuffle(shuffled)
            choices[i] = shuffled
        st.session_state.pattern_quiz_choices = choices

    if st.button("🔄 퀴즈 보기 순서 다시 섞기"):
        choices = {}
        options = [1, 2, 3, 4, 5]
        for i, item in enumerate(QUIZ_ITEMS):
            shuffled = options.copy()
            random.shuffle(shuffled)
            choices[i] = shuffled
        st.session_state.pattern_quiz_choices = choices
        st.rerun()

    score = 0
    answered = 0
    for idx, item in enumerate(QUIZ_ITEMS, start=1):
        q_index = idx - 1
        st.markdown(f"<div class='quiz-card'><div class='quiz-sentence'>Q{idx}. {esc(item['question'])}</div><div class='small-caption'>Hint: {esc(item['hint'])}</div></div>", unsafe_allow_html=True)
        options = st.session_state.pattern_quiz_choices.get(q_index, [1, 2, 3, 4, 5])
        selected = st.radio(
            "정답을 고르세요.",
            options=options,
            format_func=lambda x: f"{x}형식",
            key=f"pattern_quiz_{q_index}",
            horizontal=True,
            index=None,
        )
        if selected is not None:
            answered += 1
            if selected == item["answer"]:
                score += 1
                st.success("Correct! 구조를 잘 찾았어요.")
            else:
                st.error(f"Wrong. 정답은 {item['answer']}형식입니다.")

    st.markdown("---")
    st.metric("현재 점수", f"{score} / {len(QUIZ_ITEMS)}")
    if answered < len(QUIZ_ITEMS):
        st.info(f"아직 {len(QUIZ_ITEMS) - answered}문제가 남아 있어요.")


pattern_df = load_pattern_guide()
practice_df = load_practice_data()
verb_df = load_verb_list()

st.markdown('<div class="main-title">🧩 Pattern Guide</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">영어 문장을 1형식부터 5형식까지 나누어 보고, 구조와 대표 동사를 함께 익히는 학습 페이지입니다.</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("학습할 문장 형식", f"{len(pattern_df)}개")
with col2:
    st.metric("연결된 연습 문장", f"{len(practice_df)}개" if not practice_df.empty else "없음")
with col3:
    st.metric("연결된 동사 목록", f"{len(verb_df)}개" if not verb_df.empty else "없음")

tab1, tab2 = st.tabs(["📘 Pattern Learning", "📝 Pattern Quiz"])
with tab1:
    render_learning_tab(pattern_df, practice_df, verb_df)
with tab2:
    render_quiz_tab(pattern_df)

with st.expander("수업 활용 아이디어", expanded=False):
    st.markdown(
        """
        - 먼저 학생들에게 **한글 의미**를 읽게 한 뒤, 영어 문장의 구조를 찾게 해보세요.
        - `S`, `V`, `O`, `C` 기호를 외우게 하기보다, **누가 / 무엇을 / 어떤 상태로** 같은 질문으로 접근하면 쉽습니다.
        - Pattern Quiz를 짧게 풀고 Practice App으로 넘어가면 형식 인식이 더 자연스러워집니다.
        """
    )
