# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import pandas as pd
import re

# 각 크롤링 결과 저장하기 위한 리스트 선언
title_text = []
link_text = []
source_text = []
date_text = []
contents_text = []

# 엑셀로 저장하기 위한 변수
RESULT_PATH = '/Users/ksy/Desktop/'  # 결과 저장할 경로
now = datetime.now()  # 파일 이름 현재 시간으로 저장하기

# 날짜 정제화 함수
def date_cleansing(test):
    try:
        # 지난 뉴스
        pattern = '\\d{4}.\\d{2}.\\d{2}.'  # 정규표현식
        r = re.compile(pattern)
        match = r.search(test)
        if match:
            return match.group(0)  # 2018.11.05.
    except AttributeError:
        pass

    try:
        # 최근 뉴스
        pattern = '(\\d+)(분|시간|일|주|개월|년) 전'  # 정규표현식
        r = re.compile(pattern)
        match = r.search(test)
        if match:
            return match.group(0)
    except AttributeError:
        pass

    return ""

# 내용 정제화 함수
def contents_cleansing(contents):
    first_cleansing_contents = re.sub('<dl>.*?</a> </div> </dd> <dd>', '', str(contents)).strip()  # 앞에 필요없는 부분 제거
    first_cleansing_contents = re.sub('<ul class="relation_lst">.*?</dd>', '', first_cleansing_contents).strip()  # 뒤에 필요없는 부분 제거 (새끼 기사)
    third_cleansing_contents = re.sub('<.+?>', '', first_cleansing_contents).strip()
    return third_cleansing_contents

def crawler(maxpage, query, sort, s_date, e_date, exclude_word):
    s_from = s_date.replace(".", "")
    e_to = e_date.replace(".", "")
    page = 1
    maxpage_t = (int(maxpage) - 1) * 10 + 1  # 11= 2페이지 21=3페이지 31=4페이지 ...81=9페이지 , 91=10페이지, 101=11페이지

    while page <= maxpage_t:
        url = f"https://search.naver.com/search.naver?where=news&query={query} -{exclude_word}&sort={sort}&ds={s_date}&de={e_date}&nso=so%3Ar%2Cp%3Afrom{s_from}to{e_to}%2Ca%3A&start={str(page)}"
        response = requests.get(url)
        html = response.text

        # 뷰티풀소프의 인자값 지정
        soup = BeautifulSoup(html, 'html.parser')

        # <a>태그에서 제목과 링크주소 추출
        atags = soup.select('.news_tit')
        for atag in atags:
            title = atag.text
            link = atag['href']
            title_text.append(title)  # 제목
            link_text.append(link)    # 링크주소

        # 신문사 추출
        source_lists = soup.select('.info_group > .press')
        for source_list in source_lists:
            source_text.append(source_list.text)    # 신문사

        # 날짜 추출
        date_lists = soup.select('.info_group > span.info')
        for date_list in date_lists:
            if date_list.text.find("면") == -1:
                cleansed_date = date_cleansing(date_list.text)
                date_text.append(cleansed_date)

        # 본문요약본 추출 및 정제화
        contents_lists = soup.select('.news_dsc')
        for contents_list in contents_lists:
            cleansed_contents = contents_cleansing(contents_list)
            contents_text.append(cleansed_contents)

        page += 10

    # 리스트 길이 맞추기 (부족한 부분을 빈 문자열로 채우기)
    max_len = max(len(date_text), len(title_text), len(source_text), len(contents_text), len(link_text))

    date_text.extend([''] * (max_len - len(date_text)))
    title_text.extend([''] * (max_len - len(title_text)))
    source_text.extend([''] * (max_len - len(source_text)))
    contents_text.extend([''] * (max_len - len(contents_text)))
    link_text.extend([''] * (max_len - len(link_text)))

    # 모든 리스트 딕셔너리 형태로 저장
    result = {"date": date_text, "title": title_text, "source": source_text, "contents": contents_text, "link": link_text}
    df = pd.DataFrame(result)  # df로 변환

    # 제목이 빈 문자열인 행 전체를 제거
    df = df[df['title'] != '']

    return df

def main():
    input("=" * 50 + "\n" + "입력 형식에 맞게 입력해주세요." + "\n" + " 시작하시려면 Enter를 눌러주세요." + "\n" + "=" * 50)

    maxpage = input("최대 크롤링할 페이지 수 입력하시오 : ")
    query = input("검색어 입력 : ")
    sort = input("뉴스 검색 방식 입력(관련도순=0  최신순=1  오래된순=2) : ")    # 관련도순=0  최신순=1  오래된순=2
    s_date = input("시작날짜 입력(ex : 2019.01.04) : ")  # 2019.01.04
    e_date = input("끝날짜 입력(ex : 2019.01.05) : ")   # 2019.01.05
    exclude_word = input("제외하고 싶은 검색어 입력 : ")  # 제외하고 싶은 검색어 추가
    format_choice = input("저장할 파일 형식을 선택하세요 (1: 엑셀, 2: CSV, 3: JSON): ")

    df = crawler(maxpage, query, sort, s_date, e_date, exclude_word)

    filename = '%s-%s-%s_%s시_%s분_%s초_result' % (now.year, now.month, now.day, now.hour, now.minute, now.second)

    if format_choice == '1':
        df.to_excel(RESULT_PATH + filename + '.xlsx', sheet_name='sheet1', index=False)
    elif format_choice == '2':
        df.to_csv(RESULT_PATH + filename + '.csv', index=False)
    elif format_choice == '3':
        df.to_json(RESULT_PATH + filename + '.json')
    else:
        print("올바른 파일 형식을 선택해주세요.")

    print("데이터 수집이 완료되었습니다.")

main()
