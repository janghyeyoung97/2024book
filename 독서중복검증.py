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

    # 학생별 데이터 그룹화
    grouped = df.groupby('번호')

    for student_id, group in grouped:
        books = []

        # G열(도서 목록)에서 도서명(저자) 추출 및 병합
        for entry in group['독서활동 상황'].dropna():
            # 쉼표로 분리된 도서 목록 처리
            extracted_books = [book.strip() for book in entry.split(',') if book.strip()]
            books.extend(extracted_books)

        # 중복 검사
        seen = {}
        for idx, book in enumerate(books):
            for seen_book in seen:
                similarity = SequenceMatcher(None, book, seen_book).ratio()
                if similarity >= similarity_threshold and book != seen_book:
                    # 의심되는 도서 중복 추가
                    suspicious_results.append(f"학생 번호 {student_id}: '{book}'와 '{seen_book}' 도서가 유사합니다.")
            if book in seen:
                # 중복된 도서가 발견되면 결과에 추가
                results.append(f"학생 번호 {student_id}: '{book}' 도서가 중복 입력되었습니다.")
            else:
                seen[book] = idx

    return results, suspicious_results

# Streamlit 앱 시작
st.title("중복 도서 검출기")

# 사용 방법
st.subheader("1. 사용 방법")

# 이미지 추가
st.image("엑셀선택.jpg")

# 텍스트 추가
st.write("나이스에서 다운 받으실 때 반드시 ")
st.markdown("<span style='color:red; font-weight:bold;'>XLS data</span>로 다운받아주세요", unsafe_allow_html=True)

# 주의사항
st.subheader("2. 주의사항")
st.write("(1) 새로고침하면 다 날라갑니다!! 주의해주세요!!")
st.write("(2) 오류가 있을 수밖에 없습니다.. 꼭 한번 더 확인해주세요!")
st.write("(3) 정확하지 않은 결과가 있을 수 있으니 꼭 확인 후 수정해주세요!")

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

            # 결과 출력
            st.subheader("중복 도서 결과")
            if duplicates:
                for result in duplicates:
                    st.write(result)
            else:
                st.write("중복이 의심되는 도서가 없습니다.")

            st.subheader("중복 의심 도서 결과")
            if suspicious_duplicates:
                for result in suspicious_duplicates:
                    st.write(result)
            else:
                st.write("중복이 의심되는 도서가 없습니다.")
        else:
            st.error("G열(독서활동 상황)이 포함되지 않은 데이터입니다.")
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
