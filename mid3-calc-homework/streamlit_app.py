"""Student practice and teacher review, with a shared visual system."""
import html
import math
import os
import time
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from math_engine import build_day, check
from storage import read_submissions, save_submission

st.set_page_config(page_title='중3 계산교정 7일', page_icon='✳', layout='centered')

PASS_RATE = 90
TOTAL = 18
GROUP_SIZE = 6
START_DATE = date(2026, 9, 10)
DAY_TITLES = {
    1: '분수 기본', 2: '부호·혼합계산', 3: '번분수', 4: '제곱근',
    5: '분모의 유리화', 6: '혼합 훈련', 7: '종합 테스트',
}


def escape(value):
    return html.escape(str(value))


def secret(name, default=''):
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, KeyError):
        return default


def initialize():
    for key, value in {
        'phase': 'home', 'day': min(7, max(1, (date.today() - START_DATE).days + 1)),
        'answers': [''] * TOTAL, 'practice_group': 0, 'run_id': 0,
        'last_grade': None, 'retry_indices': None, 'admin_authenticated': False,
        'student_name': '', 'student': '', 'started_at': None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = value


def brand():
    st.markdown('''<div class="brand">
      <svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true">
        <rect width="36" height="36" rx="9" fill="#0c6557"/>
        <path d="M10 12h16M10 24h16M18 8v8" stroke="white" stroke-width="2" stroke-linecap="round"/>
        <circle cx="18" cy="20" r="1.4" fill="white"/><circle cx="18" cy="28" r="1.4" fill="white"/>
      </svg><div><div class="brand-title">계산교정 7일</div>
      <div class="brand-sub">중3 수학 · 매일 이어가는 계산훈련</div></div></div>''', unsafe_allow_html=True)


def latest_by_day(records):
    return {} if records.empty else {
        int(row['day']): row for _, row in records.drop_duplicates('day').iterrows()
    }


def status_for(accuracy):
    return '완료' if accuracy >= PASS_RATE else '재도전'


def start_practice(retry=False):
    st.session_state.phase = 'practice'
    st.session_state.practice_group = 0
    st.session_state.run_id += 1
    if not retry:
        st.session_state.student = st.session_state.student_name.strip()
        st.session_state.answers = [''] * TOTAL
        st.session_state.retry_indices = None
        st.session_state.last_grade = None
        st.session_state.started_at = time.time()
    st.rerun()


def render_home():
    st.title('계산의 기본을, 하루씩 단단하게.')
    st.markdown('<p class="hero-copy">분수부터 분모의 유리화까지. 오늘의 18문제를 풀고, 틀린 문제를 다시 확인하세요.</p>', unsafe_allow_html=True)
    left, right = st.columns([1.15, 1], gap='large')
    with left:
        st.header('오늘의 훈련')
        st.text_input('학생 이름', placeholder='예: 김학생…', key='student_name', max_chars=40)
        available_day = min(7, max(1, (date.today() - START_DATE).days + 1))
        selected = st.selectbox('훈련 선택', list(range(1, available_day + 1)),
                                index=min(st.session_state.day, available_day) - 1,
                                format_func=lambda d: f'Day {d} · {DAY_TITLES[d]}')
        st.session_state.day = selected
        st.markdown(f'''<div class="lesson-meta"><span><strong>18문항</strong> / 하루</span>
        <span><strong>17문항 이상</strong> 정답이면 통과</span></div>''', unsafe_allow_html=True)
        st.caption('6문항씩 나누어 풀어요. 종이와 필기구를 준비해 주세요.')
        if st.button('오늘의 18문제 시작', type='primary', use_container_width=True):
            if not st.session_state.student_name.strip():
                st.warning('학생 이름을 입력한 뒤 시작해 주세요.')
            else:
                start_practice()
        if st.session_state.started_at and st.session_state.last_grade is None:
            if st.button('이어서 풀기', use_container_width=True):
                st.session_state.phase = 'practice'
                st.rerun()
        with st.expander('답은 이렇게 입력해요'):
            st.markdown('분수 **`3/4`** · 제곱근 **`√5`** 또는 **`sqrt(5)`** · 곱셈 **`2*√3`**')
            st.caption('근호 앞 숫자는 붙여 쓸 수 있어요: 2√3. 분모가 여러 항이면 괄호로 묶어 주세요.')
        if st.session_state.student_name.strip():
            records = read_submissions(st.session_state.student_name.strip())
        else:
            records = pd.DataFrame()
    with right:
        st.header('7일 학습 과정')
        history = latest_by_day(records)
        rows = []
        for day, name in DAY_TITLES.items():
            if day > available_day:
                label, cls = '개방 예정', ''
            elif day in history:
                label = status_for(history[day]['accuracy'])
                cls = 'pass' if label == '완료' else 'retry'
            elif day == selected:
                label, cls = '선택한 훈련', 'current'
            else:
                label, cls = '미제출', ''
            rows.append(f'<div class="curriculum-row"><span class="day-index">Day {day}</span><span class="day-name">{name}</span><span class="status {cls}">{label}</span></div>')
        st.markdown(''.join(rows), unsafe_allow_html=True)
        st.caption('완료·재도전은 가장 최근 제출 결과를 기준으로 표시합니다.')


def submit_answers(questions):
    wrong, reasons, wrong_types = [], {}, {}
    for i, question in enumerate(questions):
        ok, reason = check(question, st.session_state.answers[i])
        if not ok:
            wrong.append(i)
            reasons[i] = reason
            category = question['category']
            wrong_types[category] = wrong_types.get(category, 0) + 1
    elapsed = max(0, int(time.time() - st.session_state.started_at))
    summary = ', '.join(f'{name} {count}문항' for name, count in wrong_types.items()) or '없음'
    try:
        attempt, accuracy = save_submission(st.session_state.student, st.session_state.day,
                                            TOTAL - len(wrong), TOTAL, elapsed, summary)
    except Exception:
        st.error('결과를 저장하지 못했습니다. 입력한 답은 유지되어 있어요. 잠시 후 다시 제출해 주세요.')
        return
    st.session_state.last_grade = {
        'score': TOTAL - len(wrong), 'accuracy': accuracy, 'wrong': wrong,
        'reasons': reasons, 'attempt': attempt, 'elapsed': elapsed, 'summary': summary,
    }
    st.session_state.phase = 'result'
    st.rerun()


def render_practice():
    day = st.session_state.day
    questions = build_day(day)
    retry = st.session_state.retry_indices is not None
    indices = st.session_state.retry_indices if retry else list(range(TOTAL))
    groups = max(1, math.ceil(len(indices) / GROUP_SIZE))
    group = min(st.session_state.practice_group, groups - 1)
    visible = indices[group * GROUP_SIZE:(group + 1) * GROUP_SIZE]
    st.title(f'Day {day} · {DAY_TITLES[day]}')
    st.caption(f'{st.session_state.student} · ' + ('오답 다시 풀기' if retry else '오늘의 계산훈련'))
    answered = sum(bool(st.session_state.answers[i].strip()) for i in indices)
    st.progress(answered / max(1, len(indices)), text=f'저장된 답 {answered}/{len(indices)} · {group + 1}/{groups}번째 묶음')
    if retry:
        st.info(f'틀린 {len(indices)}문항을 다시 풀어보세요. 최종 점수는 전체 18문항 기준입니다.')
    with st.expander('입력 도움말'):
        st.markdown('분수 **`3/4`** · 근호 **`√5`** 또는 **`sqrt(5)`** · 곱셈 **`*`** · 나눗셈 **`/`**')
        st.caption('예: 2√3/3. 덧셈이 있는 분모는 괄호로 묶어 주세요: 1/(2+√3).')
    with st.form(f'practice_{st.session_state.run_id}_{group}', clear_on_submit=False):
        inputs = {}
        for position, i in enumerate(visible):
            question = questions[i]
            st.markdown(f'<div class="question-heading"><strong>문제 {i + 1:02d}</strong><span>{escape(question["category"])}</span></div>', unsafe_allow_html=True)
            st.caption(question['prompt'])
            st.latex(question['latex'].replace(r'\frac', r'\dfrac'))
            inputs[i] = st.text_input(f'{i + 1}번 답', value=st.session_state.answers[i],
                                     key=f'answer_{st.session_state.run_id}_{i}',
                                     placeholder='예: 3/4 또는 2√3…', max_chars=120)
            grade = st.session_state.last_grade
            if retry and grade and i in grade['reasons']:
                st.caption(f'지난 제출: {grade["reasons"][i]}')
            if position < len(visible) - 1:
                st.divider()
        st.caption('아래 버튼을 누르면 이 묶음의 답이 유지됩니다. 브라우저를 닫기 전 제출해 주세요.')
        prev_col, next_col = st.columns(2)
        with prev_col:
            previous = st.form_submit_button('이전 6문항', disabled=group == 0, use_container_width=True)
        with next_col:
            next_group = st.form_submit_button('다음 6문항', disabled=group == groups - 1, use_container_width=True)
        submit = st.form_submit_button('전체 답 제출하고 채점하기' if not retry else '오답 제출하고 다시 채점하기',
                                       type='primary', use_container_width=True)
    if previous or next_group or submit:
        for i, value in inputs.items():
            st.session_state.answers[i] = value
        if submit:
            missing = [i + 1 for i, value in enumerate(st.session_state.answers) if not value.strip()]
            if missing:
                st.warning('아직 답이 없는 문제가 있어요: ' + ', '.join(map(str, missing)) + '번. 답을 입력한 뒤 제출해 주세요.')
            else:
                submit_answers(questions)
        else:
            st.session_state.practice_group = group + (1 if next_group else -1)
            st.rerun()


def render_result():
    grade = st.session_state.last_grade
    passed = grade['accuracy'] >= PASS_RATE
    st.title('오늘의 훈련 결과')
    st.caption(f'{st.session_state.student} · Day {st.session_state.day} · {DAY_TITLES[st.session_state.day]}')
    title = '오늘의 훈련을 완료했어요.' if passed else '틀린 문제를 한 번 더 확인해요.'
    description = '17문항 이상을 맞혀 통과했습니다.' if passed else f'통과까지 {17 - grade["score"]}문항을 더 맞히면 됩니다.'
    st.markdown(f'''<div class="result"><span class="status {'pass' if passed else 'retry'}">{'완료' if passed else '재도전'}</span>
      <h2>{title}</h2><div class="result-score">{grade['score']} <small>/ 18문항</small></div><p>{description}</p></div>''', unsafe_allow_html=True)
    first, second, third = st.columns(3)
    first.metric('정확도', f'{grade["accuracy"]}%')
    second.metric('제출 횟수', f'{grade["attempt"]}회')
    third.metric('총 풀이 시간', f'{grade["elapsed"] // 60}분 {grade["elapsed"] % 60}초')
    st.caption('풀이 시간은 이번 훈련을 시작한 뒤의 경과 시간이며 재도전 시간을 포함합니다.')
    if grade['wrong']:
        st.header('다시 확인할 유형')
        st.write(grade['summary'])
        if st.button(f'틀린 {len(grade["wrong"])}문항 다시 풀기', type='primary', use_container_width=True):
            st.session_state.retry_indices = grade['wrong']
            start_practice(retry=True)
    if st.button('학습 과정으로 돌아가기', type='primary' if not grade['wrong'] else 'secondary', use_container_width=True):
        st.session_state.phase = 'home'
        st.rerun()
    with st.expander('문항별 제출 결과'):
        questions = build_day(st.session_state.day)
        for i, question in enumerate(questions):
            label = '정답' if i not in grade['wrong'] else '다시 확인'
            st.markdown(f'**{i + 1}번 · {label}**')
            st.latex(question['latex'].replace(r'\frac', r'\dfrac'))
            st.write('입력한 답:', st.session_state.answers[i])
            if i in grade['wrong']:
                st.caption(grade['reasons'][i])


def render_teacher():
    st.title('학생의 학습 흐름을 한눈에.')
    st.markdown('<p class="hero-copy">오늘 확인할 학생부터 살펴보고, 제출 기록과 재도전 결과를 확인하세요.</p>', unsafe_allow_html=True)
    if not st.session_state.admin_authenticated:
        admin_pin = str(os.environ.get('HOMEWORK_ADMIN_PIN') or secret('admin_pin'))
        if not admin_pin:
            st.info('교사 화면의 접속 설정이 필요합니다. 운영 담당자에게 문의해 주세요.')
            return
        with st.form('teacher_login'):
            st.header('교사 접속')
            pin = st.text_input('관리자 PIN', type='password', placeholder='발급받은 PIN 입력…')
            login = st.form_submit_button('학생 결과 확인', type='primary', use_container_width=True)
        if login:
            if pin == admin_pin:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error('PIN이 일치하지 않습니다. 다시 확인해 주세요.')
        return
    if st.button('교사 화면 로그아웃'):
        st.session_state.admin_authenticated = False
        st.rerun()
    day = st.selectbox('확인할 훈련', range(1, 8), index=st.session_state.day - 1,
                       format_func=lambda d: f'Day {d} · {DAY_TITLES[d]}', key='teacher_day')
    all_records = read_submissions()
    if all_records.empty:
        st.info('아직 제출한 학생이 없습니다. 학생에게 학습 주소를 안내하면 첫 제출부터 여기에 표시됩니다.')
        return
    st.caption('학생 목록은 한 번 이상 제출한 이름을 기준으로 구성됩니다. 아직 한 번도 제출하지 않은 학생은 포함되지 않습니다.')
    rows = []
    for student in sorted(all_records['student'].unique()):
        records = all_records[(all_records['student'] == student) & (all_records['day'] == day)]
        if records.empty:
            rows.append({'학생': student, '상태': '미제출', '첫 점수': None, '최근 점수': None, '시도': 0, '최근 제출': '—'})
        else:
            latest, first = records.iloc[0], records.iloc[-1]
            rows.append({'학생': student, '상태': status_for(latest['accuracy']),
                         '첫 점수': first['accuracy'], '최근 점수': latest['accuracy'],
                         '시도': int(latest['attempt']), '최근 제출': latest['submitted_at'].replace('T', ' ')})
    table = pd.DataFrame(rows)
    counts = table['상태'].value_counts()
    st.markdown(f'''<div class="summary-strip"><span>미제출<strong>{counts.get('미제출', 0)}</strong></span>
    <span>재도전<strong>{counts.get('재도전', 0)}</strong></span><span>완료<strong>{counts.get('완료', 0)}</strong></span></div>''', unsafe_allow_html=True)
    search_col, filter_col = st.columns([1.3, 1])
    with search_col:
        search = st.text_input('학생 검색', placeholder='학생 이름 검색…', max_chars=40)
    with filter_col:
        status = st.selectbox('학습 상태', ['전체', '미제출', '재도전', '완료'])
    filtered = table[table['학생'].str.contains(search.strip(), regex=False)]
    if status != '전체':
        filtered = filtered[filtered['상태'] == status]
    rank = {'미제출': 0, '재도전': 1, '완료': 2}
    filtered = filtered.assign(_rank=filtered['상태'].map(rank)).sort_values(['_rank', '학생']).drop(columns='_rank')
    st.header(f'Day {day} 학습 현황')
    if filtered.empty:
        st.info('조건에 맞는 학생이 없습니다. 검색어나 학습 상태를 바꿔보세요.')
    else:
        st.dataframe(filtered, hide_index=True, use_container_width=True,
                     column_config={'첫 점수': st.column_config.NumberColumn(format='%.1f%%'),
                                    '최근 점수': st.column_config.NumberColumn(format='%.1f%%')})
    st.download_button('현재 목록 CSV 다운로드', filtered.to_csv(index=False).encode('utf-8-sig'),
                       f'Day{day}_학습현황.csv', 'text/csv', use_container_width=True)
    with st.expander('전체 제출 기록과 백업'):
        export = all_records.rename(columns={'submitted_at': '제출시각', 'student': '학생', 'day': 'Day',
            'attempt': '시도', 'score': '점수', 'total': '총문제', 'accuracy': '정확도',
            'elapsed_sec': '소요초', 'wrong_types': '오답유형'}).drop(columns='id')
        st.dataframe(export, use_container_width=True, hide_index=True)
        st.download_button('전체 제출 기록 CSV 다운로드', export.to_csv(index=False).encode('utf-8-sig'),
                           '중3_계산숙제_제출결과.csv', 'text/csv', use_container_width=True)
        st.caption('현재는 로컬 저장 방식입니다. 호스팅 환경에 따라 재배포 시 기록이 사라질 수 있으므로 전체 기록을 정기적으로 백업해 주세요.')


initialize()
st.markdown('<style>' + Path(__file__).with_name('ui.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)
brand()
view = st.radio('사용 화면', ['학생 학습', '교사 관리'], horizontal=True, key='view', label_visibility='collapsed')
st.divider()
try:
    if view == '교사 관리':
        render_teacher()
    elif st.session_state.phase == 'practice':
        render_practice()
    elif st.session_state.phase == 'result':
        render_result()
    else:
        render_home()
except Exception:
    st.error('화면을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')
    st.stop()
st.markdown('<div class="footnote">하루 18문항 · 총 7일 / 126문항 · 통과 기준 90% 이상</div>', unsafe_allow_html=True)
