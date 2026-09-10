import streamlit as st
import sqlite3, random, math, re
from datetime import datetime, date
from fractions import Fraction
import sympy as sp
import pandas as pd

st.set_page_config(page_title='중3 계산교정 7일', page_icon='🧮', layout='centered')

PASS_RATE = 90
DB_PATH = 'homework.db'
START_DATE = date(2026, 9, 10)

DAY_TITLES = {
    1: '분수 기본', 2: '부호·혼합계산', 3: '번분수', 4: '제곱근',
    5: '분모의 유리화', 6: '혼합 훈련', 7: '종합 테스트'
}

# ---------- DB ----------
def db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submitted_at TEXT NOT NULL,
        student TEXT NOT NULL,
        day INTEGER NOT NULL,
        attempt INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        accuracy REAL NOT NULL,
        elapsed_sec INTEGER NOT NULL,
        wrong_types TEXT NOT NULL
    )''')
    con.commit()
    return con

CON = db()

def next_attempt(student, day):
    row = CON.execute('SELECT COUNT(*) FROM submissions WHERE student=? AND day=?', (student, day)).fetchone()
    return int(row[0]) + 1

def save_submission(student, day, score, total, elapsed, wrong_types):
    acc = round(score / total * 100, 1)
    attempt = next_attempt(student, day)
    CON.execute('INSERT INTO submissions(submitted_at,student,day,attempt,score,total,accuracy,elapsed_sec,wrong_types) VALUES(?,?,?,?,?,?,?,?,?)',
                (datetime.now().isoformat(timespec='seconds'), student, day, attempt, score, total, acc, elapsed, wrong_types))
    CON.commit()
    return attempt, acc

# ---------- question generation ----------
def sf(rng, a=1, b=9, d1=2, d2=10):
    return sp.Rational(rng.choice([1,-1])*rng.randint(a,b), rng.randint(d1,d2))

def addq(out, latex, ans, cat, prompt='계산하시오.', rationalized=False, simplified=False):
    out.append(dict(latex=latex, ans=sp.simplify(ans), category=cat, prompt=prompt,
                    rationalized=rationalized, simplified=simplified))

def build_day(day):
    rng = random.Random(20260910 + day)
    out=[]
    if day == 1:
        for _ in range(18):
            A, B = sf(rng,d2=12), sf(rng,d2=12)
            op=rng.choice(['+','-','\\times','\\div'])
            ans={'+':A+B,'-':A-B,'\\times':A*B,'\\div':A/B}[op]
            addq(out, f'{sp.latex(A)} {op} {sp.latex(B)}', ans, '분수 사칙연산')
    elif day == 2:
        for i in range(18):
            a,b,c=sf(rng),sf(rng),sf(rng)
            if i%3==0:
                addq(out,f'{sp.latex(a)}+\\left({sp.latex(b)}\\right)\\times {sp.latex(c)}',a+b*c,'부호·혼합계산')
            elif i%3==1:
                addq(out,f'{sp.latex(a)}-\\left({sp.latex(b)}\\right)\\div {sp.latex(c)}',a-b/c,'부호·혼합계산')
            else:
                addq(out,f'\\left({sp.latex(a)}+{sp.latex(b)}\\right)\\times {sp.latex(c)}',(a+b)*c,'부호·혼합계산')
    elif day == 3:
        for i in range(18):
            a=sp.Rational(rng.randint(1,8),rng.randint(2,9)); b=sp.Rational(rng.randint(1,8),rng.randint(2,9))
            if i<9:
                addq(out,f'\\frac{{{sp.latex(a)}}}{{{sp.latex(b)}}}',a/b,'번분수')
            else:
                c=sp.Rational(rng.randint(1,8),rng.randint(2,9)); d=sp.Rational(rng.randint(1,8),rng.randint(2,9))
                if c==d: d += sp.Rational(1,7)
                addq(out,f'\\frac{{{sp.latex(a)}+{sp.latex(b)}}}{{{sp.latex(c)}-{sp.latex(d)}}}',(a+b)/(c-d),'번분수')
    elif day == 4:
        rad=[8,12,18,20,24,27,32,45,48,50,72,75,98]
        for i in range(18):
            if i<8:
                n=rad[i%len(rad)]
                addq(out,f'\\sqrt{{{n}}}',sp.sqrt(n),'제곱근','가장 간단한 근호의 꼴로 나타내시오.',simplified=True)
            elif i<13:
                r=rng.choice([2,3,5,7]); k1=rng.randint(1,4); k2=rng.randint(1,4); n2=r*rng.choice([4,9])
                addq(out,f'{k1}\\sqrt{{{r}}}+{k2}\\sqrt{{{n2}}}',k1*sp.sqrt(r)+k2*sp.sqrt(n2),'제곱근','가장 간단히 하시오.',simplified=True)
            else:
                r1,r2=rng.choice([(2,8),(3,12),(5,20),(2,18),(3,27)]); k=rng.randint(1,4)
                addq(out,f'{k}\\sqrt{{{r1}}}\\times\\sqrt{{{r2}}}',k*sp.sqrt(r1)*sp.sqrt(r2),'제곱근','계산하여 가장 간단히 하시오.',simplified=True)
    elif day == 5:
        for i in range(18):
            if i<12:
                a=rng.randint(1,9); n=rng.choice([2,3,5,6,7,10,11,13]); b=rng.randint(1,4)
                expr=sp.Rational(a,b)/sp.sqrt(n)
                latex=f'\\frac{{{a}}}{{\\sqrt{{{n}}}}}' if b==1 else f'\\frac{{{a}}}{{{b}\\sqrt{{{n}}}}}'
                addq(out,latex,sp.radsimp(expr),'분모 유리화','분모를 유리화하시오.',True,True)
            else:
                a=rng.randint(1,6); n=rng.choice([2,3,5,6,7]); m=rng.randint(1,4)
                addq(out,f'\\frac{{{a}\\sqrt{{{m}}}}}{{\\sqrt{{{n}}}}}',sp.radsimp(a*sp.sqrt(m)/sp.sqrt(n)),'분모 유리화','분모를 유리화하여 가장 간단히 하시오.',True,True)
    else:
        def mixed(kind):
            if kind==0:
                a,b,c=sf(rng),sf(rng),sf(rng)
                addq(out,f'{sp.latex(a)}+\\left({sp.latex(b)}\\right)\\times {sp.latex(c)}',a+b*c,'혼합계산' if day==6 else '종합')
            elif kind==1:
                a=sp.Rational(rng.randint(1,8),rng.randint(2,9)); b=sp.Rational(rng.randint(1,8),rng.randint(2,9)); c=sp.Rational(rng.randint(1,8),rng.randint(2,9)); d=sp.Rational(rng.randint(1,8),rng.randint(2,9))
                addq(out,f'\\frac{{{sp.latex(a)}-{sp.latex(b)}}}{{{sp.latex(c)}+{sp.latex(d)}}}',(a-b)/(c+d),'혼합계산' if day==6 else '종합')
            elif kind==2:
                r=rng.choice([2,3,5,7]); k1=rng.randint(1,4); k2=rng.randint(1,4); n2=r*rng.choice([4,9])
                addq(out,f'{k1}\\sqrt{{{r}}}-{k2}\\sqrt{{{n2}}}',k1*sp.sqrt(r)-k2*sp.sqrt(n2),'혼합계산' if day==6 else '종합','가장 간단히 하시오.',False,True)
            else:
                a=rng.randint(1,9); n=rng.choice([2,3,5,6,7,10,11,13])
                addq(out,f'\\frac{{{a}}}{{\\sqrt{{{n}}}}}',sp.radsimp(a/sp.sqrt(n)),'혼합계산' if day==6 else '종합','분모를 유리화하시오.',True,True)
        for i in range(18): mixed(i%4 if day==6 else [0,0,1,2,3][i%5])
    return out

# ---------- answer checking ----------
def parse_answer(text):
    s=text.strip().replace(' ', '').replace('−','-').replace('×','*').replace('÷','/')
    s=re.sub(r'√\((\d+)\)', r'sqrt(\1)', s)
    s=re.sub(r'√(\d+)', r'sqrt(\1)', s)
    s=re.sub(r'(\d|\))sqrt\(', r'\1*sqrt(', s)
    if not re.fullmatch(r'[0-9+\-*/().a-zA-Z]+', s): raise ValueError
    if re.sub('sqrt','',s,flags=re.I).isalpha(): raise ValueError
    if re.search(r'[a-zA-Z]', re.sub('sqrt','',s,flags=re.I)): raise ValueError
    return sp.sympify(s, locals={'sqrt':sp.sqrt})

def denominator_has_radical(raw):
    s=raw.replace(' ','')
    p=s.rfind('/')
    if p<0: return False
    den=s[p+1:]
    return '√' in den or 'sqrt' in den.lower()

def reducible_radical(raw):
    nums=[int(x) for x in re.findall(r'√\(?(\d+)\)?', raw)] + [int(x) for x in re.findall(r'sqrt\((\d+)\)', raw, re.I)]
    for n in nums:
        for k in range(2,int(math.sqrt(n))+1):
            if n%(k*k)==0: return True
    return False

def check(q, raw):
    if not raw.strip(): return False, '답을 입력하지 않았습니다.'
    try: val=parse_answer(raw)
    except Exception: return False, '입력 형식을 확인하세요.'
    try:
        if sp.simplify(val-q['ans']) != 0: return False, '계산 결과가 다릅니다.'
    except Exception: return False, '입력 형식을 확인하세요.'
    if q['rationalized'] and denominator_has_radical(raw): return False, '분모의 유리화가 완료되지 않았습니다.'
    if q['simplified'] and reducible_radical(raw): return False, '근호를 더 간단히 할 수 있습니다.'
    return True, ''

# ---------- UI ----------
st.markdown('''<style>
.block-container{max-width:760px;padding-top:1.4rem;padding-bottom:3rem}
[data-testid="stMetric"]{background:#fff;border:1px solid #eee;padding:10px;border-radius:12px}
.small{color:#6b7280;font-size:.9rem}.ok{color:#15803d;font-weight:800}.bad{color:#b91c1c;font-weight:800}
</style>''', unsafe_allow_html=True)

st.title('🧮 중3 계산교정 7일')
st.caption('하루 18문제 · 분수 → 번분수 → 제곱근 → 유리화 → 종합')

if 'started' not in st.session_state: st.session_state.started=False
if 'start_ts' not in st.session_state: st.session_state.start_ts=None
if 'last_grade' not in st.session_state: st.session_state.last_grade=None

student=st.text_input('학생 이름', placeholder='예: 김학생')
today_day=max(1,min(7,(date.today()-START_DATE).days+1))
cols=st.columns(7)
selected=st.session_state.get('day',today_day)
for i,c in enumerate(cols,1):
    with c:
        if st.button(f'D{i}', disabled=i>today_day, use_container_width=True, key=f'daybtn{i}'):
            st.session_state.day=i; selected=i; st.session_state.started=False; st.session_state.last_grade=None; st.rerun()
selected=st.session_state.get('day',selected)
st.info(f'Day {selected} · {DAY_TITLES[selected]}')

if not st.session_state.started:
    if st.button('숙제 시작', type='primary', use_container_width=True, disabled=not student.strip()):
        st.session_state.started=True
        st.session_state.start_ts=datetime.now().timestamp()
        st.session_state.student=student.strip()
        st.session_state.day=selected
        st.session_state.answers=['']*18
        st.session_state.last_grade=None
        st.rerun()
else:
    student=st.session_state.student; selected=st.session_state.day
    qs=build_day(selected)
    wrong_only = st.session_state.get('retry_wrong', None)
    visible_indices = wrong_only if wrong_only else list(range(18))
    st.write(f'**{student} · Day {selected}**')
    for i in visible_indices:
        q=qs[i]
        st.markdown(f'**{i+1}번**  ·  <span class="small">{q["category"]}</span>', unsafe_allow_html=True)
        st.caption(q['prompt'])
        st.latex(q['latex'])
        st.session_state.answers[i]=st.text_input('답', value=st.session_state.answers[i], key=f'ans_{selected}_{i}', label_visibility='collapsed', placeholder='예: 3/4, sqrt(5), √5')
        if st.session_state.last_grade and i in st.session_state.last_grade['reasons']:
            st.error(st.session_state.last_grade['reasons'][i])
        st.divider()

    if st.button('제출하고 채점하기' if not wrong_only else '오답 다시 제출하기', type='primary', use_container_width=True):
        results=[]; reasons={}; wrong_types={}; score=0; wrong=[]
        for i,q in enumerate(qs):
            ok,reason=check(q,st.session_state.answers[i])
            results.append(ok)
            if ok: score+=1
            else:
                wrong.append(i); reasons[i]=reason; wrong_types[q['category']]=wrong_types.get(q['category'],0)+1
        elapsed=int(datetime.now().timestamp()-st.session_state.start_ts)
        summary=', '.join(f'{k} {v}개' for k,v in wrong_types.items()) or '없음'
        attempt,acc=save_submission(student,selected,score,18,elapsed,summary)
        st.session_state.last_grade={'score':score,'acc':acc,'wrong':wrong,'reasons':reasons,'attempt':attempt,'elapsed':elapsed,'summary':summary}
        if acc>=PASS_RATE:
            st.session_state.retry_wrong=None
        else:
            st.session_state.retry_wrong=wrong
            st.session_state.start_ts=datetime.now().timestamp()
        st.rerun()

    g=st.session_state.last_grade
    if g:
        c1,c2,c3=st.columns(3)
        c1.metric('점수',f"{g['score']}/18"); c2.metric('정확도',f"{g['acc']}%"); c3.metric('시도',f"{g['attempt']}회")
        if g['acc']>=PASS_RATE:
            st.success('통과했습니다. (90% 이상)')
        else:
            st.warning(f"90% 미만입니다. 틀린 {len(g['wrong'])}문제만 다시 풀어주세요.")

with st.expander('선생님 결과 보기'):
    pin=st.text_input('관리자 PIN',type='password')
    admin_pin=str(st.secrets.get('admin_pin','2580')) if hasattr(st,'secrets') else '2580'
    if st.button('결과 조회'):
        if pin!=admin_pin:
            st.error('PIN이 올바르지 않습니다.')
        else:
            df=pd.read_sql_query('SELECT submitted_at AS 제출시각, student AS 학생, day AS Day, attempt AS 시도, score AS 점수, total AS 총문제, accuracy AS 정확도, elapsed_sec AS 소요초, wrong_types AS 오답유형 FROM submissions ORDER BY id DESC',CON)
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button('CSV 다운로드',df.to_csv(index=False).encode('utf-8-sig'),'중3_계산숙제_제출결과.csv','text/csv',use_container_width=True)
            st.caption('현재 버전은 Streamlit Community Cloud 로컬 SQLite에 저장합니다. 서버 재시작/재배포 시 데이터가 유실될 수 있으므로 CSV를 주기적으로 내려받으세요.')
