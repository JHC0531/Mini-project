
import html
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from gtts import gTTS
    from gtts.tts import gTTSError
    GTTS_AVAILABLE = True
except Exception:
    gTTS = None
    gTTSError = Exception
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
    "1": {"bg": "#E8F3FF", "border": "#5DADE2", "badge": "#2874A6", "soft": "#F4FAFF"},
    "2": {"bg": "#EFFFF6", "border": "#58D68D", "badge": "#1E8449", "soft": "#F6FFFA"},
    "3": {"bg": "#FFF4E6", "border": "#F5B041", "badge": "#B9770E", "soft": "#FFFBF4"},
    "4": {"bg": "#F5EDFF", "border": "#AF7AC5", "badge": "#76448A", "soft": "#FBF7FF"},
    "5": {"bg": "#FFEFF3", "border": "#EC7063", "badge": "#B03A2E", "soft": "#FFF7F8"},
}

TYPE_COLORS = {
    "regular": {"bg": "#EAF7EA", "text": "#1E7D32", "label": "규칙동사"},
    "irregular": {"bg": "#FFF0E5", "text": "#B85C00", "label": "불규칙동사"},
    "phrasal": {"bg": "#EEF0FF", "text": "#3F51B5", "label": "구동사"},
}

DEFAULT_PATTERN_COLOR = {"bg": "#F4F6F7", "border": "#AAB7B8", "badge": "#566573", "soft": "#FAFAFA"}
DEFAULT_TYPE_COLOR = {"bg": "#F4F6F7", "text": "#566573", "label": "기타"}

# ------------------------------------------------------------
# CSS
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .main-header {
        padding: 1.4rem 1.6rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #F0F7FF 0%, #FFF7EA 52%, #F9F0FF 100%);
        border: 1px solid #E3E8EF;
        margin-bottom: 1.1rem;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.15rem;
        line-height: 1.2;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.05rem;
        color: #475467;
    }
    .metric-card {
        padding: 1rem 1.1rem;
        border-radius: 22px;
        background: #FFFFFF;
        border: 1px solid #EAECF0;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.07);
        min-height: 110px;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #667085;
        font-weight: 700;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 900;
        color: #1D2939;
        margin-top: 0.25rem;
    }
    .table-wrap {
        width: 100%;
        overflow-x: auto;
        border-radius: 22px;
        border: 1px solid #E4E7EC;
        box-shadow: 0 8px 24px rgba(16, 24, 40, 0.08);
        margin-top: 0.75rem;
    }
    table.pretty-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 1.02rem;
        background: white;
    }
    .pretty-table th {
        position: sticky;
        top: 0;
        z-index: 1;
        background: #344054;
        color: white;
        padding: 0.95rem 0.8rem;
        text-align: left;
        font-size: 1rem;
        letter-spacing: 0.01em;
    }
    .pretty-table td {
        padding: 0.95rem 0.8rem;
        border-bottom: 1px solid #EAECF0;
        vertical-align: top;
        line-height: 1.5;
    }
    .verb-word {
        font-size: 1.25rem;
        font-weight: 900;
        color: #101828;
        letter-spacing: 0.01em;
    }
    .meaning-text {
        font-size: 1.08rem;
        font-weight: 800;
        color: #1D2939;
    }
    .example-text {
        color: #344054;
        font-size: 1rem;
    }
    .badge {
        display: inline-block;
        padding: 0.28rem 0.58rem;
        border-radius: 999px;
        color: white;
        font-weight: 900;
        font-size: 0.92rem;
        white-space: nowrap;
    }
    .type-badge {
        display: inline-block;
        padding: 0.28rem 0.58rem;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.9rem;
        white-space: nowrap;
    }
    .audio-card {
        padding: 1rem;
        border-radius: 22px;
        margin: 0.75rem 0 0.35rem 0;
        border-left-width: 9px;
        border-left-style: solid;
        box-shadow: 0 4px 14px rgba(16, 24, 40, 0.06);
    }
    .card-verb {
        font-size: 1.48rem;
        font-weight: 950;
        color: #101828;
    }
    .card-meaning {
        font-size: 1.07rem;
        font-weight: 800;
        color: #344054;
        margin-top: 0.25rem;
    }
    .card-example {
        margin-top: 0.5rem;
        padding: 0.7rem 0.85rem;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.75);
        color: #344054;
        font-size: 1.02rem;
    }
    .audio-guide {
        padding: 0.9rem 1rem;
        border-radius: 18px;
        background: #F9FAFB;
        border: 1px solid #EAECF0;
        color: #344054;
        margin-bottom: 0.8rem;
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
        "1": "1형식",
        "2": "2형식",
        "3": "3형식",
        "4": "4형식",
        "5": "5형식",
    }).fillna(df["pattern"] + "형식")

    df["type_label"] = df["type"].map({
        "regular": "규칙동사",
        "irregular": "불규칙동사",
        "phrasal": "구동사",
    }).fillna(df["type"])

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


def get_pattern_color(pattern: str) -> dict:
    return PATTERN_COLORS.get(str(pattern), DEFAULT_PATTERN_COLOR)


def get_type_color(verb_type: str) -> dict:
    return TYPE_COLORS.get(str(verb_type), DEFAULT_TYPE_COLOR)


def safe_text(value) -> str:
    return html.escape(str(value))


def make_html_table(table_df: pd.DataFrame) -> str:
    if table_df.empty:
        return """
        <div style='padding:1.2rem;border-radius:18px;background:#FFF7E6;border:1px solid #F5B041;'>
            조건에 맞는 동사가 없습니다. 검색어나 필터를 바꿔보세요.
        </div>
        """

    rows_html = []
    for _, row in table_df.iterrows():
        pattern = str(row["pattern"])
        verb_type = str(row["type"])
        p_color = get_pattern_color(pattern)
        t_color = get_type_color(verb_type)

        rows_html.append(
            f"""
            <tr>
                <td style="background:{p_color['bg']}; border-left:8px solid {p_color['border']};">
                    <span class="badge" style="background:{p_color['badge']};">{safe_text(row['pattern_label'])}</span>
                </td>
                <td style="background:{p_color['soft']};">
                    <span class="verb-word">{safe_text(row['verb'])}</span>
                </td>
                <td style="background:{p_color['soft']};">
                    <span class="type-badge" style="background:{t_color['bg']}; color:{t_color['text']};">{safe_text(row['type_label'])}</span>
                </td>
                <td style="background:{p_color['soft']};">
                    <span class="meaning-text">{safe_text(row['korean_meaning'])}</span>
                </td>
                <td style="background:{p_color['soft']};">
                    <span class="example-text">{safe_text(row['example'])}</span>
                </td>
            </tr>
            """
        )

    return f"""
    <div class="table-wrap">
        <table class="pretty-table">
            <thead>
                <tr>
                    <th style="width: 110px;">문장 형식</th>
                    <th style="width: 150px;">동사</th>
                    <th style="width: 120px;">유형</th>
                    <th style="width: 180px;">한글 뜻</th>
                    <th>예문</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    """


def render_metric_card(label: str, value: str, emoji: str, bg_color: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card" style="background:{bg_color};">
            <div class="metric-label">{emoji} {safe_text(label)}</div>
            <div class="metric-value">{safe_text(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_audio_player(text: str, player_key: str) -> None:
    try:
        with st.spinner("오디오를 만드는 중입니다..."):
            audio_bytes = make_tts_audio(text)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception as error:
        st.error("오디오를 만들 수 없습니다.")
        st.caption("Streamlit Cloud에서는 requirements.txt에 gTTS가 포함되어 있어야 하고, 인터넷 연결이 필요합니다.")
        st.caption(f"오류 내용: {error}")


def render_audio_card(row: pd.Series, row_number: int) -> None:
    pattern = str(row["pattern"])
    color = get_pattern_color(pattern)
    type_color = get_type_color(str(row["type"]))

    st.markdown(
        f"""
        <div class="audio-card" style="background:{color['bg']}; border-left-color:{color['border']};">
            <div>
                <span class="badge" style="background:{color['badge']};">{safe_text(row['pattern_label'])}</span>
                <span class="type-badge" style="background:{type_color['bg']}; color:{type_color['text']}; margin-left:0.35rem;">{safe_text(row['type_label'])}</span>
            </div>
            <div class="card-verb">{safe_text(row['verb'])}</div>
            <div class="card-meaning">뜻: {safe_text(row['korean_meaning'])}</div>
            <div class="card-example">예문: {safe_text(row['example'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    button_col1, button_col2, button_col3 = st.columns([1.2, 1.3, 4])
    word_key = f"word_audio_{row_number}_{row['verb']}"
    example_key = f"example_audio_{row_number}_{row['verb']}"

    with button_col1:
        word_clicked = st.button("🔊 단어 듣기", key=word_key, use_container_width=True)
    with button_col2:
        example_clicked = st.button("🔊 예문 듣기", key=example_key, use_container_width=True)

    if word_clicked:
        st.session_state.active_audio = {
            "key": word_key,
            "text": str(row["verb"]),
            "label": f"단어: {row['verb']}",
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
        render_audio_player(active_audio["text"], active_audio["key"])


# ------------------------------------------------------------
# Main app
# ------------------------------------------------------------
df = load_verb_list(VERB_LIST_PATH)

st.markdown(
    """
    <div class="main-header">
        <h1>📚 Verb List</h1>
        <p>문장 형식별 핵심 동사를 색깔로 구분하고, 재생 버튼으로 단어와 예문 발음을 들어요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not GTTS_AVAILABLE:
    st.warning("gTTS 패키지가 설치되어 있지 않아 오디오 기능을 사용할 수 없습니다. requirements.txt에 gTTS를 추가하세요.")

col1, col2, col3 = st.columns(3)
with col1:
    render_metric_card("전체 동사 수", f"{len(df)}개", "✅", "#F0F7FF")
with col2:
    render_metric_card("문장 형식", f"{df['pattern'].nunique()}개", "🧩", "#F5EDFF")
with col3:
    render_metric_card("동사 유형", f"{df['type'].nunique()}개", "⭐", "#FFF4E6")

st.markdown("---")

st.subheader("🎨 색깔로 보는 문장 형식")
legend_cols = st.columns(5)
for i, pattern in enumerate(["1", "2", "3", "4", "5"]):
    color = get_pattern_color(pattern)
    with legend_cols[i]:
        st.markdown(
            f"""
            <div style="padding:0.7rem;border-radius:16px;background:{color['bg']};border:2px solid {color['border']};text-align:center;font-weight:900;color:{color['badge']};">
                {pattern}형식
            </div>
            """,
            unsafe_allow_html=True,
        )

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
st.caption("먼저 표로 전체 단어를 훑어본 뒤, 아래 카드에서 발음을 들어보세요.")
st.markdown(make_html_table(filtered_df), unsafe_allow_html=True)

st.markdown("---")

st.subheader("🔊 Audio Practice Cards")
st.markdown(
    """
    <div class="audio-guide">
        <b>단어 듣기</b>는 동사 하나만 읽어주고, <b>예문 듣기</b>는 전체 예문을 읽어줍니다. 
        처음 누를 때는 gTTS가 오디오를 만드는 데 잠시 시간이 걸릴 수 있습니다.
    </div>
    """,
    unsafe_allow_html=True,
)

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
