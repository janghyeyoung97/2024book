import streamlit as st
import pandas as pd
import re

# 페이지 제목
st.title("자율활동 날짜 형식 검증기")

# 페이지 설명
st.write("""
자율활동 파일을 다운받아 올려주세요! 
항목별 파일로 받으셔야 하고 반드시 XLS data파일로 올려주세요.
""")

# 파일 업로드 기능
uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx", "xls"])

# 날짜 형식 검증 함수
def validate_date_format_final(date_str):
    errors = []
    
    # (1) . 빠짐: .이 빠져있는 경우
    if re.match(r"\(\d{4}\d{2}\d{2}-\d{4}\d{2}\d{2}\)", date_str):  # '.' 빠짐
        errors.append(". 빠짐")
    
    # (2) - 빠짐: ~이 있으면
    if re.match(r"\(\d{4}\.\d{2}\.\d{2}~\d{4}\.\d{2}\.\d{2}/\d+회\)", date_str):  # ~이 포함된 날짜
        errors.append("- 빠짐")
    
    # (3) 기타 오류: 위에서 나온 것 외에 다른 오류들
    if not re.match(r"\(2024\.\d{2}\.\d{2}[\.,\-\/\d\w]*\)", date_str):
        errors.append("기타 오류(-확인, 오타 확인, /확인 등등)")
    
    # (4) 2회 삭제: /2회 포함된 경우 오류, -를 ,로 바꿨는지도 확인
    if re.search(r"/2회", date_str):
        errors.append("2회 삭제(-를 ,로 바꿨는지도 확인)")
    
    # 오류가 없으면 빈칸
    if len(errors) == 0:
        return ""
    
    # 오류가 있으면 오류 내용을 반환
    return ', '.join(errors)

if uploaded_file is not None:
    # 엑셀 파일 읽기
    df_new = pd.read_excel(uploaded_file)

    # 자율활동에 해당하는 행만 필터링
    df_filtered = df_new[df_new['Unnamed: 2'] == '자율활동']  # 3번째 열에서 '자율활동'만 추출

    # 날짜 형식 추출
    date_info_filtered = []
    for idx, activity in df_filtered['Unnamed: 4'].items():  # 자율활동 데이터에서 특기사항 열 확인
        if isinstance(activity, str):  # 문자열일 때만 처리
            date_matches = re.findall(r"\(2024\.[^\)]*\)", activity)  # "(2024."로 시작하는 모든 부분 추출
            for date_str in date_matches:
                date_info_filtered.append((df_filtered['Unnamed: 0'][idx], date_str))  # 학생 번호와 날짜를 매칭

    # 날짜 검증을 적용한 새로운 DataFrame
    date_df_filtered = pd.DataFrame(date_info_filtered, columns=['학생 번호', '날짜'])

    # 오류 검증을 적용
    date_df_filtered['오류 검증'] = date_df_filtered['날짜'].apply(validate_date_format_final)

    # 학생 번호가 0인 부분을 위의 값으로 채우기
    date_df_filtered['학생 번호'] = date_df_filtered['학생 번호'].fillna(0).astype(int)

    # 결과를 표로 보여주기 (가로 크기 확장 및 열 너비 조정)
    st.write("자율활동 날짜 정보 및 오류 검증 결과")

    # 열 너비 스타일 설정
    styled_df = date_df_filtered.style.set_table_styles(
        [
            {'selector': 'th', 'props': [('font-size', '16px')]},  # 헤더 글자 크기
            {'selector': 'col0', 'props': [('width', '50px')]},  # 학생 번호 열 너비 줄이기
            {'selector': 'col1', 'props': [('width', '150px')]},  # 날짜 열 너비 조정
            {'selector': 'col2', 'props': [('width', '300px')]},  # 오류 검증 열 너비 늘리기
        ],
        overwrite=True
    )
    
    st.dataframe(styled_df, use_container_width=True)

    # 추가 내용 설명
    st.write("""
    1. 오류 검증 열이 빈칸이라면 올바르게 입력한 것입니다.

    2. 오류 검증에 오류 내용이 있다면 확인해주세요.

    
    (1) 2회 삭제 : 횟수가 2회인 경우 '/2회' 이 부분이 삭제되어야 합니다. 그리고 -로 날짜가 연결되어있진 않은지 확인해주세요.
    
    (2) 기타 오류 : - 대신 ~이 쓰인 경우, 오타가 있는 경우, 어딘가 이상한 경우 기타오류로 분류합니다. 오류가 아닐수도 있으나 한번씩 확인 해주셔야 하는 부분입니다.

    내용이 잘려서 보이는 경우 표에 마우스를 올리시면 표 우측 상단에 확대해서 볼 수 있는 기능이 뜹니다. (맨 오른쪽 아이콘)
    """)
