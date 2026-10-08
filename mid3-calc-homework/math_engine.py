import random
import math
import re
import sympy as sp

# Original question generation and grading rules, preserved for this UI pass.

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


