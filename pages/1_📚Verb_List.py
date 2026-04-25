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

st.set_page_config(
    page_title="Verb List",
    page_icon="📚",
    layout="wide",
)

# ------------------------------------------------------------
# File path helper
# Works whether this file is placed in the root folder or pages/.
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Color settings
# ------------------------------------------------------------
PATTERN_COLORS = {
    "1": {"soft": "#F4FAFF", "main": "#2874A6", "name": "Blue"},
    "2": {"soft": "#F6FFFA", "main": "#1E8449", "name": "Green"},
    "3": {"soft": "#FFFBF4", "main": "#B9770E", "name": "Orange"},
    "4": {"soft": "#FBF7FF", "main": "#76448A", "name": "Purple"},
    "5": {"soft": "#FFF7F8", "main": "#B03A2E", "name": "Pink"},
}

TYPE_LABELS = {
    "regular": "규칙동사",
    "irregular": "불규칙동사",
    "phrasal": "구동사",
}

TYPE_COLORS = {
    "regular": "#EAF7EA",
    "irregular": "#FFF0E5",
    "phrasal": "#EEF0FF",
}

TYPE_TEXT_COLORS = {
    "regular": "#1E7D32",
    "irregular": "#B85C00",
    "phrasal": "#3F51B5",
}

# ------------------------------------------------------------
# Data loading
# ------------------------------------------------------------
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
        "1": "1형식",
        "2": "2형식",
        "3": "3형식",
        "4": "4형식",
        "5": "5형식",
    }).fillna(df["pattern"] + "형식")

    df["type_label"] = df["type"].map(TYPE_LABELS).fillna(df["type"])

    return df


@st.cache_data(show_spinner=False, max_entries=300)
def make_tts_audio(text: str, lang: str = "en") -> bytes:
    """Create mp3 bytes with gTTS. Internet connection is required."""
    if not GTTS_AVAILABLE:
        raise RuntimeError("gTTS 패키지가 설치되어 있지 않습니다. requirements.txt에 gTTS를 추가하세요.")

    fp = BytesIO()
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()


def clean_word_for_audio(verb: str) -> str:
    """Remove teacher notes such as '(device)' before TTS reads the word."""
    cleaned = re.sub(r"\s*\([^)]*\)", "", str(verb)).strip()
    return cleaned or str(verb)


def render_audio_player(text: str) -> None:
    try:
        with st.spinner("오디오를 만드는 중입니다..."):
            audio_bytes = make_tts_audio(text)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception as error:
        st.error("오디오를 만들 수 없습니다.")
        st.caption("Streamlit Cloud에서는 requirements.txt에 gTTS가 포함되어 있어야 하고, 인터넷 연결이 필요합니다.")
        st.caption(f"오류 내용: {error}")


def style_verb_table(display_df: pd.DataFrame):
    """Use pandas Styler instead of raw HTML so the table will not appear as code."""
    def row_style(row):
        pattern_value = str(row.get("문장 형식", "")).replace("형식", "")
        bg = PATTERN_COLORS.get(pattern_value, {"soft": "#FFFFFF"})["soft"]
        return [
            f"background-color: {bg}; color: #111111; font-size: 16px; font-weight: 600;"
            for _ in row
        ]

    return (
        display_df.style
        .apply(row_style, axis=1)
        .set_properties(**{
            "color": "#111111",
            "border-color": "#E4E7EC",
            "text-align": "left",
        })
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", "#EEF4FF"),
                    ("color", "#111111"),
                    ("font-weight", "900"),
                    ("font-size", "16px"),
                    ("text-align", "left"),
                    ("border", "1px solid #D0D5DD"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("color", "#111111"),
                    ("border", "1px solid #EAECF0"),
                ],
            },
        ])
    )


def render_pattern_legend() -> None:
    legend_cols = st.columns(5)
    for i, pattern in enumerate(["1", "2", "3", "4", "5"]):
        color = PATTERN_COLORS[pattern]
        with legend_cols[i]:
            st.markdown(
                f"""
                <div style="padding:0.8rem;border-radius:16px;background:{color['soft']};border:2px solid {color['main']};text-align:center;font-weight:900;color:#111111;">
                    <span style="color:{color['main']};">●</span> {pattern}형식
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_audio_card(row: pd.Series, row_number: int) -> None:
    pattern = str(row["pattern"])
    color = PATTERN_COLORS.get(pattern, {"soft": "#FFFFFF", "main": "#667085"})

    with st.container(border=True):
        top_cols = st.columns([1, 1, 3])
        with top_cols[0]:
            st.markdown(f"**{row['pattern_label']}**")
        with top_cols[1]:
            st.markdown(f"**{row['type_label']}**")
        with top_cols[2]:
            st.markdown(f"<span style='color:{color['main']}; font-weight:900;'>●</span> <b>{row['verb']}</b>", unsafe_allow_html=True)

        st.markdown(f"**뜻:** {row['korean_meaning']}")
        st.markdown(f"**예문:** {row['example']}")

        button_col1, button_col2, button_col3 = st.columns([1.2, 1.3, 4])
        word_key = f"word_audio_{row_number}_{row['verb']}"
        example_key = f"example_audio_{row_number}_{row['verb']}"

        with button_col1:
            word_clicked = st.button("🔊 단어 듣기", key=word_key, use_container_width=True)
        with button_col2:
            example_clicked = st.button("🔊 예문 듣기", key=example_key, use_container_width=True)

        if word_clicked:
            word_text = clean_word_for_audio(row["verb"])
            st.session_state.active_audio = {
                "key": word_key,
                "text": word_text,
                "label": f"단어: {word_text}",
            }
        if example_clicked:
            st.session_state.active_audio = {
                "key": example_key,
                "text": str(row["example"]),
                "label": f"예문: {row['example']}",
            }

        active_audio = st.session_state.get("active_audio")
        if active_audio and active_audio.get("key") in {word_key, example_key}:
            st.caption(active_audio["label"])
            render_audio_player(active_audio["text"])


# ------------------------------------------------------------
# Main app
# ------------------------------------------------------------
df = load_verb_list(VERB_LIST_PATH)

st.title("📚 Verb List")
st.caption("문장 형식별 핵심 동사를 색깔로 구분하고, 재생 버튼으로 단어와 예문 발음을 들어요.")

if not GTTS_AVAILABLE:
    st.warning("gTTS 패키지가 설치되어 있지 않아 오디오 기능을 사용할 수 없습니다. requirements.txt에 gTTS를 추가하세요.")

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("전체 동사 수", f"{len(df)}개")
metric_col2.metric("문장 형식", f"{df['pattern'].nunique()}개")
metric_col3.metric("동사 유형", f"{df['type'].nunique()}개")

st.markdown("---")
st.subheader("🎨 색깔로 보는 문장 형식")
render_pattern_legend()

st.markdown("---")
st.subheader("🔎 동사 찾기")
filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])

with filter_col1:
    pattern_values = sorted(df["pattern"].unique(), key=lambda x: int(x) if str(x).isdigit() else 999)
    pattern_options = ["전체"] + [f"{p}형식" for p in pattern_values]
    selected_pattern_label = st.selectbox("문장 형식", pattern_options)

with filter_col2:
    type_options = ["전체"] + sorted(df["type_label"].unique().tolist())
    selected_type = st.selectbox("동사 유형", type_options)

with filter_col3:
    search_word = st.text_input("동사 / 한글 뜻 / 예문 검색", placeholder="예: arrive, 도착하다, airport")

filtered_df = df.copy()

if selected_pattern_label != "전체":
    selected_pattern = selected_pattern_label.replace("형식", "")
    filtered_df = filtered_df[filtered_df["pattern"] == selected_pattern]

if selected_type != "전체":
    filtered_df = filtered_df[filtered_df["type_label"] == selected_type]

if search_word.strip():
    keyword = search_word.strip().lower()
    filtered_df = filtered_df[
        filtered_df["verb"].str.lower().str.contains(keyword, na=False)
        | filtered_df["korean_meaning"].str.lower().str.contains(keyword, na=False)
        | filtered_df["example"].str.lower().str.contains(keyword, na=False)
    ]

st.success(f"현재 조건에 맞는 동사: {len(filtered_df)}개")

st.subheader("🌈 Colorful Verb Table")
st.caption("표는 HTML을 사용하지 않고 Streamlit 표로 렌더링합니다. 그래서 코드가 화면에 그대로 뜨지 않습니다.")

if filtered_df.empty:
    st.warning("조건에 맞는 동사가 없습니다. 검색어나 필터를 바꿔보세요.")
else:
    display_df = filtered_df[["pattern_label", "verb", "type_label", "korean_meaning", "example"]].rename(columns={
        "pattern_label": "문장 형식",
        "verb": "동사",
        "type_label": "유형",
        "korean_meaning": "한글 뜻",
        "example": "예문",
    })

    st.dataframe(
        style_verb_table(display_df),
        use_container_width=True,
        hide_index=True,
        height=min(620, 70 + len(display_df) * 42),
    )

st.markdown("---")
st.subheader("🔊 Audio Practice Cards")
st.info("단어 듣기는 동사 하나만 읽어주고, 예문 듣기는 전체 예문을 읽어줍니다. 처음 누를 때는 오디오 생성에 잠시 시간이 걸릴 수 있습니다.")

if filtered_df.empty:
    st.warning("조건에 맞는 동사가 없습니다. 검색어나 필터를 바꿔보세요.")
else:
    for row_number, (_, row) in enumerate(filtered_df.reset_index(drop=True).iterrows()):
        render_audio_card(row, row_number)

with st.expander("💡 수업 활용 팁"):
    st.markdown(
        """
        - 학생들이 먼저 단어 발음을 듣고 따라 말한 뒤, 예문 발음을 듣게 하면 좋습니다.
        - 같은 형식의 동사끼리 필터링한 뒤 한 묶음으로 읽기 연습을 시킬 수 있습니다.
        - 오디오는 gTTS로 즉석 생성되므로, Streamlit Cloud에서 인터넷 연결이 필요합니다.
        - 자주 누른 단어와 예문은 캐시에 저장되어 다시 누를 때 더 빠르게 재생됩니다.
        """
    )
