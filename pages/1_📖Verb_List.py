from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import streamlit as st

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except Exception:
    gTTS = None
    GTTS_AVAILABLE = False

st.set_page_config(page_title="Verb List", page_icon="📚", layout="wide")

CURRENT_DIR = Path(__file__).resolve().parent
POSSIBLE_BASE_DIRS = [CURRENT_DIR, CURRENT_DIR.parent]


def find_file(filename: str) -> Path:
    for base_dir in POSSIBLE_BASE_DIRS:
        candidate = base_dir / filename
        if candidate.exists():
            return candidate
    st.error(f"파일을 찾을 수 없습니다: {filename}")
    st.info("이 파일은 앱 파일과 같은 폴더 또는 한 단계 위 폴더에 있어야 합니다.")
    st.stop()


VERB_LIST_PATH = find_file("verb list.csv")

PATTERN_COLORS = {
    "1": {"soft": "#F4FAFF", "main": "#2874A6", "border": "#5DADE2"},
    "2": {"soft": "#F6FFFA", "main": "#1E8449", "border": "#58D68D"},
    "3": {"soft": "#FFFBF4", "main": "#B9770E", "border": "#F5B041"},
    "4": {"soft": "#FBF7FF", "main": "#76448A", "border": "#AF7AC5"},
    "5": {"soft": "#FFF7F8", "main": "#B03A2E", "border": "#F1948A"},
}

st.markdown(
    """
    <style>
    .verb-card {
        background: #FFFFFF;
        border: 1px solid #E4E7EC;
        border-left: 10px solid #98A2B3;
        border-radius: 22px;
        padding: 22px 24px;
        margin: 8px 0 18px 0;
        box-shadow: 0 8px 22px rgba(16, 24, 40, 0.08);
        min-height: 250px;
        color: #111111 !important;
    }
    .verb-word-main {
        font-size: 2.35rem;
        font-weight: 950;
        line-height: 1.1;
        margin-bottom: 12px;
        color: #111111 !important;
    }
    .verb-detail {
        font-size: 1.02rem;
        line-height: 1.65;
        color: #222222 !important;
        margin: 3px 0;
    }
    .pattern-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 5px 11px;
        font-weight: 900;
        color: white !important;
        font-size: 0.88rem;
        margin-bottom: 10px;
    }
    .soft-note {
        font-size: 0.94rem;
        opacity: 0.88;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_verb_list(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    required_columns = ["verb", "type", "pattern", "korean_meaning", "example"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error("verb list.csv에 필요한 열이 없습니다.")
        st.write("빠진 열:", missing_columns)
        st.stop()

    df = df[required_columns].copy()
    for col in required_columns:
        df[col] = df[col].astype(str).str.strip()

    df["pattern"] = df["pattern"].str.replace(".0", "", regex=False)
    df["pattern_label"] = df["pattern"].map({
        "1": "1형식", "2": "2형식", "3": "3형식", "4": "4형식", "5": "5형식",
    }).fillna(df["pattern"] + "형식")
    return df


@st.cache_data(show_spinner=False, max_entries=300)
def make_tts_audio(text: str, lang: str = "en") -> bytes:
    if not GTTS_AVAILABLE:
        raise RuntimeError("gTTS 패키지가 설치되어 있지 않습니다. requirements.txt에 gTTS를 추가하세요.")
    fp = BytesIO()
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()


def clean_word_for_audio(verb: str) -> str:
    cleaned = re.sub(r"\s*\([^)]*\)", "", str(verb)).strip()
    return cleaned or str(verb)


def render_audio_player(text: str) -> None:
    try:
        with st.spinner("오디오를 만드는 중입니다..."):
            audio_bytes = make_tts_audio(text)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception as error:
        st.error("오디오를 만들 수 없습니다.")
        st.caption("requirements.txt에 gTTS가 포함되어 있어야 하고, 인터넷 연결이 필요합니다.")
        st.caption(f"오류 내용: {error}")


def style_verb_table(display_df: pd.DataFrame):
    def row_style(row):
        pattern_value = str(row.get("문장 형식", "")).replace("형식", "")
        bg = PATTERN_COLORS.get(pattern_value, {"soft": "#FFFFFF"})["soft"]
        return [f"background-color: {bg}; color: #111111; font-size: 16px; font-weight: 650;" for _ in row]

    return (
        display_df.style
        .apply(row_style, axis=1)
        .set_properties(**{"color": "#111111", "border-color": "#E4E7EC", "text-align": "left"})
        .set_table_styles([
            {"selector": "th", "props": [("background-color", "#EEF4FF"), ("color", "#111111"), ("font-weight", "900"), ("font-size", "16px"), ("text-align", "left"), ("border", "1px solid #D0D5DD")]},
            {"selector": "td", "props": [("color", "#111111"), ("border", "1px solid #EAECF0")]},
        ])
    )


def render_pattern_legend() -> None:
    cols = st.columns(5)
    for i, pattern in enumerate(["1", "2", "3", "4", "5"]):
        color = PATTERN_COLORS[pattern]
        with cols[i]:
            st.markdown(
                f"""
                <div style="padding:0.8rem;border-radius:16px;background:{color['soft']};border:2px solid {color['border']};text-align:center;font-weight:900;color:#111111;">
                    <span style="color:{color['main']};">●</span> {pattern}형식
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_audio_card(row: pd.Series, row_number: int) -> None:
    pattern = str(row["pattern"])
    color = PATTERN_COLORS.get(pattern, {"soft": "#FFFFFF", "main": "#667085", "border": "#98A2B3"})
    card_html = f"""
    <div class="verb-card" style="border-left-color:{color['border']}; background:{color['soft']};">
        <span class="pattern-pill" style="background:{color['main']};">{row['pattern_label']}</span>
        <div class="verb-word-main">{row['verb']}</div>
        <div class="verb-detail"><b>뜻</b> · {row['korean_meaning']}</div>
        <div class="verb-detail"><b>예문</b> · {row['example']}</div>
        <div class="verb-detail soft-note"><b>형식</b> · {row['pattern_label']}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    btn_col1, btn_col2 = st.columns(2)
    word_key = f"word_audio_{row_number}_{row['verb']}"
    example_key = f"example_audio_{row_number}_{row['verb']}"
    with btn_col1:
        word_clicked = st.button("🔊 단어 듣기", key=word_key, use_container_width=True)
    with btn_col2:
        example_clicked = st.button("🔊 예문 듣기", key=example_key, use_container_width=True)

    if word_clicked:
        word_text = clean_word_for_audio(row["verb"])
        st.session_state.active_audio = {"key": word_key, "text": word_text, "label": f"단어: {word_text}"}
    if example_clicked:
        st.session_state.active_audio = {"key": example_key, "text": str(row["example"]), "label": f"예문: {row['example']}"}

    active_audio = st.session_state.get("active_audio")
    if active_audio and active_audio.get("key") in {word_key, example_key}:
        st.caption(active_audio["label"])
        render_audio_player(active_audio["text"])


# Main
df = load_verb_list(VERB_LIST_PATH)

st.title("📚 Verb List")
st.caption("문장 형식별 핵심 동사를 살펴보고, 단어와 예문 발음을 들어보는 페이지입니다.")

if not GTTS_AVAILABLE:
    st.warning("gTTS 패키지가 설치되어 있지 않아 오디오 기능을 사용할 수 없습니다. requirements.txt에 gTTS를 추가하세요.")

metric_col1, metric_col2 = st.columns(2)
metric_col1.metric("전체 동사 수", f"{len(df)}개")

st.markdown("---")
st.subheader("🎨 색깔로 보는 문장 형식")
render_pattern_legend()

st.markdown("---")
st.subheader("🔎 동사 찾기")
filter_col1, filter_col2 = st.columns([1, 2])
with filter_col1:
    pattern_values = sorted(df["pattern"].unique(), key=lambda x: int(x) if str(x).isdigit() else 999)
    pattern_options = ["전체"] + [f"{p}형식" for p in pattern_values]
    selected_pattern_label = st.selectbox("문장 형식", pattern_options)
with filter_col2:
    search_word = st.text_input("동사 / 한글 뜻 / 예문 검색", placeholder="예: arrive, 도착하다, airport")

filtered_df = df.copy()
if selected_pattern_label != "전체":
    selected_pattern = selected_pattern_label.replace("형식", "")
    filtered_df = filtered_df[filtered_df["pattern"] == selected_pattern]
if search_word.strip():
    keyword = search_word.strip().lower()
    filtered_df = filtered_df[
        filtered_df["verb"].str.lower().str.contains(keyword, na=False)
        | filtered_df["korean_meaning"].str.lower().str.contains(keyword, na=False)
        | filtered_df["example"].str.lower().str.contains(keyword, na=False)
    ]

st.success(f"현재 조건에 맞는 동사: {len(filtered_df)}개")

st.subheader("🌈 Colorful Verb Table")
st.caption("유형 정보는 제외하고, 동사·뜻·예문·문장 형식만 간단히 확인합니다.")
if filtered_df.empty:
    st.warning("조건에 맞는 동사가 없습니다. 검색어나 필터를 바꿔보세요.")
else:
    display_df = filtered_df[["pattern_label", "verb", "korean_meaning", "example"]].rename(columns={
        "pattern_label": "문장 형식",
        "verb": "동사",
        "korean_meaning": "한글 뜻",
        "example": "예문",
    })
    st.dataframe(style_verb_table(display_df), use_container_width=True, hide_index=True, height=min(620, 70 + len(display_df) * 42))

st.markdown("---")
st.subheader("🔊 Audio Practice Cards")
st.info("단어를 먼저 보고, 뜻과 예문을 확인한 뒤 발음을 들어보세요.")

if filtered_df.empty:
    st.warning("조건에 맞는 동사가 없습니다. 검색어나 필터를 바꿔보세요.")
else:
    rows = list(filtered_df.reset_index(drop=True).iterrows())
    for i in range(0, len(rows), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(rows):
                row_number, row = rows[i + j]
                with cols[j]:
                    render_audio_card(row, row_number)

with st.expander("💡 수업 활용 팁"):
    st.markdown(
        """
        - 학생들이 먼저 큰 글씨의 동사를 읽고, 뜻과 예문을 확인하게 해보세요.
        - 같은 형식의 동사끼리 필터링한 뒤 한 묶음으로 읽기 연습을 할 수 있습니다.
        - 단어 듣기는 동사 하나만, 예문 듣기는 전체 예문을 읽어줍니다.
        """
    )
