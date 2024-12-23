import streamlit as st
import pandas as pd
from difflib import SequenceMatcher

# 중복 도서 검출 함수
def find_duplicates_by_student(df, similarity_threshold=0.7):
    results = []
    suspicious_results = []

    # 번호 열에서 빈칸을 채우기 (학생 번호 이어지도록 처리)
    df['번호'] = df['번호'].fillna(method='ffill')

    # 페이지 구분 행(A~G열이 NaN이거나, 4행의 헤더가 다시 나타나는 경우 제거)
    df = df.dropna(subset=df.columns[:7], how='all')
    df = df[df['번호'] != '번호']  # 중간에 반복된 헤더 제거

    # 빈 칸 채우기 (과목 또는 영역, 학년도, 학년, 학기)
    columns_to_fill = ['과목 또는 영역', '학년도', '학년', '학기']
    df[columns_to_fill] = df[columns_to_fill].ffill()

    # 학생별 데이터 그룹화
    grouped = df.groupby('번호')

    for student_id, group in grouped:
        seen_books = {}

        # G열(도서 목록)에서 도서명(저자) 추출 및 병합
        for _, row in group.iterrows():
            subject = row['과목 또는 영역']
            year = row['학년도']
            grade = row['학년']
            semester = row['학기']
            books = [book.strip() for book in str(row['독서활동 상황']).split(',') if book.strip()]

            for book in books:
                # 중복 검사
                if book in seen_books:
                    # 중복된 도서가 발견되면 결과에 추가
                    results.append({
                        '학생 번호': student_id,
                        '중복 도서명': book,
                        '중복 도서 위치': f"{seen_books[book]}, {subject}/{year}/{grade}/{semester}"
                    })
                else:
                    # 첫 번째로 등장한 도서 기록
                    seen_books[book] = f"{subject}/{year}/{grade}/{semester}"

                # 의심되는 도서 검사 (유사성 기준 적용)
                for seen_book in seen_books:
                    similarity = SequenceMatcher(None, book, seen_book).ratio()
                    if similarity >= similarity_threshold and book != seen_book:
                        suspicious_results.append({
                            '학생 번호': student_id,
                            '도서 A': book,
                            '도서 B': seen_book,
                            '중복 위치': f"{seen_books[seen_book]}, {subject}/{year}/{grade}/{semester}"
                        })

    return results, suspicious_results

# Streamlit 앱 시작
st.title("중복 도서 검출기")

# 사용 방법
st.subheader("1. 사용 방법")

# 가로 배치: 1*2 구조로 설명과 이미지를 추가
col1, col2 = st.columns(2)

# 왼쪽: (1) 설명과 '엑셀선택.jpg'
with col1:
    st.markdown("(1) 나이스에서 다운 받으실 때 반드시 **<span style='color:red; font-weight:bold;'>XLS data</span>**로 다운받아주세요", unsafe_allow_html=True)
    st.image("엑셀선택.jpg", use_container_width=True)

# 오른쪽: (2) 설명과 '행삭제.jpg'
with col2:
    st.markdown("(2) 파일을 다운받으신 후 열어서 **<span style='color:red; font-weight:bold;'>B열</span>의 학생 이름 열을 **<span style='color:red; font-weight:bold;'>통째로 삭제</span>**해주세요!", unsafe_allow_html=True)
    st.image("행삭제.jpg", use_container_width=True)

# 주의사항
st.subheader("2. 주의사항")
st.write("(1) 새로고침하면 다 날라갑니다!! 주의해주세요!!")
st.write("(2) 오류가 있을 수밖에 없습니다.. 꼭 한번 더 확인해주세요!")

# 파일 업로드
st.subheader("3. 독서활동상황 파일 업로드")
uploaded_file = st.file_uploader("독서활동 상황 엑셀 파일을 업로드하세요", type=['xlsx', 'xls'])
st.write("파일을 업로드하면 중복 도서가 검출됩니다.")

if uploaded_file:
    # 파일 읽기
    try:
        # 전체 데이터 로드
        df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
        st.success("파일이 성공적으로 업로드되었습니다.")

        # 데이터 미리보기
        st.write("전체 데이터 미리보기:")
        st.dataframe(df)

        # 데이터 전처리: 헤더와 데이터 분리
        header_row = 3  # 헤더가 있는 행
        df.columns = df.iloc[header_row]  # 헤더 설정
        df = df[(header_row + 1):]  # 데이터만 유지
        df.reset_index(drop=True, inplace=True)  # 인덱스 초기화

        # G열 확인 및 중복 검사 실행
        if '독서활동 상황' in df.columns:
            duplicates, suspicious_duplicates = find_duplicates_by_student(df)

            # 결과 출력: 중복 도서
            st.subheader("중복 도서 결과")
            st.write("도서명이 100% 동일한 경우 나타납니다.")
            if duplicates:
                current_student = None
                for result in duplicates:
                    if current_student != result['학생 번호']:
                        if current_student is not None:
                            st.write("")  # 줄바꿈 추가
                        current_student = result['학생 번호']
                        st.markdown(f"#### **학생 번호 {current_student}**")
                    st.write(f"- 도서명: '{result['중복 도서명']}'")
                    st.write(f"- 위치: {result['중복 도서 위치']}")
            else:
                st.write("중복이 의심되는 도서가 없습니다.")

            # 결과 출력: 중복 의심 도서
            st.subheader("중복 의심 도서 결과")
            st.write("저자명이 동일하거나, 띄어쓰기를 제외한 책 제목이 동일하거나, 3글자 이상 유사한 경우가 나타납니다. 이상이 없는 경우 무시하고, 이상이 있는 경우 수정이 필요합니다.")
            if suspicious_duplicates:
                current_student = None
                for result in suspicious_duplicates:
                    if current_student != result['학생 번호']:
                        if current_student is not None:
                            st.write("")  # 줄바꿈 추가
                        current_student = result['학생 번호']
                        st.markdown(f"#### **학생 번호 {current_student}**")
                    st.write(f"- 도서 A: '{result['도서 A']}'")
                    st.write(f"- 도서 B: '{result['도서 B']}'")
                    st.write(f"- 위치: {result['중복 위치']}")
            else:
                st.write("중복이 의심되는 도서가 없습니다.")
        else:
            st.error("G열(독서활동 상황)이 포함되지 않은 데이터입니다.")
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
