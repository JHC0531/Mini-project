# Verb Practice App

## GitHub에 올릴 파일
- verb_practice_app.py
- data.csv
- verb list.csv
- pattern guide.xlsx
- requirements.txt

## Streamlit Cloud 설정
Main file path:

```text
verb_practice_app.py
```

## 이번 버전의 핵심 수정
- correct_verb, option_b, option_c, option_d의 위치가 문항마다 랜덤으로 섞입니다.
- Streamlit rerun 때문에 채점이 꼬이지 않도록, 한 번 표시된 문항의 보기 순서는 현재 풀이 중에는 고정됩니다.
- `처음부터 다시 풀기`를 누르면 문제 순서와 보기 순서가 다시 랜덤으로 섞입니다.
- 문장 Category가 앱 상단에 표시됩니다.
