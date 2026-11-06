"""NEON CASINO - запуск: python neon_casino.py  (нічого встановлювати не треба)"""
import json, random, socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8000
RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
PLAYERS = {}
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SYMS = ["🍒", "🍋", "🔔", "⭐", "💎", "7️⃣"]
BETS = ("slots", "roulette", "dice", "coin", "bjdeal")


def draw():
    return random.choice(RANKS) + random.choice("♠♥♦♣")


def hv(hand):
    t = a = 0
    for c in hand:
        r = c[:-1]
        if r == "A":
            t += 11
            a += 1
        elif r in ("10", "J", "Q", "K"):
            t += 10
        else:
            t += int(r)
    while t > 21 and a:
        t -= 10
        a -= 1
    return t


def bj_finish(g, p):
    pv = hv(g["p"])
    if pv <= 21:
        while hv(g["d"]) < 17:
            g["d"].append(draw())
    dv = hv(g["d"])
    nat = pv == 21 and len(g["p"]) == 2
    if pv > 21:
        w = 0
    elif nat and not (dv == 21 and len(g["d"]) == 2):
        w = int(g["bet"] * 2.5)
    elif dv > 21 or pv > dv:
        w = g["bet"] * 2
    elif pv == dv:
        w = g["bet"]
    else:
        w = 0
    g["done"], g["win"] = True, w
    p["bal"] += w


def bj_view(g, p):
    d = g["done"]
    return {"player": g["p"], "dealer": g["d"] if d else [g["d"][0], "?"],
            "pv": hv(g["p"]), "dv": hv(g["d"]) if d else None,
            "done": d, "win": g["win"], "bet": g["bet"], "balance": p["bal"]}


def play(pid, game, body):
    p = PLAYERS.setdefault(pid, {"bal": 1000, "bj": None})
    if game == "state":
        return {"balance": p["bal"]}
    if game == "reset":
        p["bal"], p["bj"] = 1000, None
        return {"balance": 1000}
    bet = 0
    if game in BETS:
        bet = int(body.get("bet", 0))
        if bet < 10 or bet > p["bal"]:
            return {"error": "Недостатньо монет 💸", "balance": p["bal"]}
        p["bal"] -= bet
    win, extra = 0, {}
    if game == "slots":
        r = random.choices(SYMS, weights=[30, 25, 20, 15, 7, 3], k=3)
        if len(set(r)) == 1:
            win = bet * {"7️⃣": 50, "💎": 25}.get(r[0], 10)
        elif len(set(r)) == 2:
            win = int(bet * 1.5)
        extra = {"reels": r}
    elif game == "roulette":
        n = random.randint(0, 36)
        col = "green" if n == 0 else ("red" if n in RED else "black")
        k = body.get("kind")
        if (k == "red" and col == "red") or (k == "black" and col == "black"):
            win = bet * 2
        elif (k == "zero" and n == 0) or (k == "num" and n == int(body.get("num", -1))):
            win = bet * 36
        extra = {"n": n, "color": col}
    elif game == "dice":
        a, b = random.randint(1, 6), random.randint(1, 6)
        pick = body.get("pick")
        if (pick == "low" and a + b < 7) or (pick == "high" and a + b > 7):
            win = bet * 2
        extra = {"dice": [a, b]}
    elif game == "coin":
        res = random.choice(["eagle", "tails"])
        if res == body.get("pick"):
            win = bet * 2
        extra = {"result": res}
    elif game == "bjdeal":
        g = {"p": [draw(), draw()], "d": [draw(), draw()], "bet": bet, "done": False, "win": 0}
        p["bj"] = g
        if hv(g["p"]) == 21:
            bj_finish(g, p)
        return bj_view(g, p)
    elif game in ("bjhit", "bjstand"):
        g = p["bj"]
        if not g or g["done"]:
            return {"error": "Нема активної гри", "balance": p["bal"]}
        if game == "bjhit":
            g["p"].append(draw())
            if hv(g["p"]) >= 21:
                bj_finish(g, p)
        else:
            bj_finish(g, p)
        return bj_view(g, p)
    else:
        return {"error": "?", "balance": p["bal"]}
    p["bal"] += win
    return {"balance": p["bal"], "win": win, "bet": bet, **extra}


HTML = r"""<!doctype html>
<html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0618"><meta name="apple-mobile-web-app-capable" content="yes">
<title>Neon Casino</title>
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;min-height:100vh;background:radial-gradient(circle at 50% -10%,#3b1470,#0b0618 60%) fixed;color:#f2e9ff;font-family:system-ui,-apple-system,sans-serif;padding-bottom:90px;user-select:none}
header{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;padding-top:calc(12px + env(safe-area-inset-top));position:sticky;top:0;background:#0b0618d9;backdrop-filter:blur(10px);z-index:5}
.logo{font-weight:900;letter-spacing:3px;color:#e0a8ff;text-shadow:0 0 14px #b44cff,0 0 30px #b44cff}
.pill{background:#1c0f3a;border:1px solid #b44cff;border-radius:99px;padding:6px 14px;box-shadow:0 0 14px #b44cff66;font-weight:800}
main{max-width:460px;margin:0 auto;padding:4px 16px}
.box{background:#ffffff0a;border:1px solid #b44cff44;border-radius:20px;padding:18px;margin-top:12px;box-shadow:inset 0 0 30px #7a2cff22}
h2{margin:0 0 10px;font-size:18px;color:#e0a8ff;text-shadow:0 0 10px #b44cff}
.chips{display:flex;gap:10px;justify-content:center;margin-top:6px}
.chip{width:54px;height:54px;border-radius:50%;border:3px dashed #fff8;background:#4b1d9a;color:#fff;font-weight:800;transition:.2s}
.chip.on{background:#c02cff;box-shadow:0 0 18px #ff3df2;transform:scale(1.14)}
.btn{width:100%;padding:15px;border:0;border-radius:14px;background:linear-gradient(90deg,#7a2cff,#ff3df2);color:#fff;font-weight:800;font-size:16px;box-shadow:0 0 20px #b44cff88;margin-top:14px;transition:.1s}
.btn:active{transform:scale(.96)}.row{display:flex;gap:10px}.row .btn{flex:1}
.opts{display:flex;gap:8px;margin-top:10px}
.opt{flex:1;padding:11px 4px;border-radius:12px;border:1px solid #b44cff66;background:#1c0f3a;color:#cbb6f5;font-weight:700}
.opt.on{background:#7a2cff;color:#fff;box-shadow:0 0 14px #b44cff}
input[type=number]{width:100%;margin-top:10px;padding:12px;border-radius:12px;border:1px solid #b44cff66;background:#1c0f3a;color:#fff;font-size:16px}
.hint{text-align:center;color:#9a86c4;font-size:13px;margin:14px 0 0}
nav{position:fixed;bottom:0;left:0;right:0;display:flex;background:#0b0618ee;backdrop-filter:blur(12px);border-top:1px solid #b44cff55;padding:6px 4px calc(6px + env(safe-area-inset-bottom));z-index:5}
nav button{flex:1;background:none;border:0;color:#9a86c4;font-size:11px;display:flex;flex-direction:column;align-items:center;gap:2px}
nav button span{font-size:24px}nav button.on{color:#ff9cf8;text-shadow:0 0 10px #ff3df2}nav button.on span{filter:drop-shadow(0 0 8px #ff3df2)}
.machine{position:relative;margin:6px 40px 0 0;background:linear-gradient(#2a1060,#150a30);border:3px solid #b44cff;border-radius:22px;padding:20px;box-shadow:0 0 30px #b44cff88}
.reels{display:flex;gap:10px}
.reel{flex:1;height:110px;display:flex;align-items:center;justify-content:center;font-size:62px;background:#08031a;border-radius:12px;border:2px solid #3df5ff55;box-shadow:inset 0 0 20px #000}
.reel.spin{filter:blur(2px);animation:shake .1s infinite}.reel.stop{animation:bounce .35s}
.machine.win{animation:glow .5s 4}
.lever{position:absolute;right:-38px;top:26px;width:34px;height:124px;transition:transform .35s ease-in;cursor:pointer}
.lever .stick{position:absolute;left:14px;top:14px;width:6px;height:100px;background:linear-gradient(90deg,#999,#fff,#777);border-radius:3px}
.lever .ball{position:absolute;left:0;top:-4px;width:34px;height:34px;border-radius:50%;background:radial-gradient(circle at 30% 30%,#ff9cf8,#ff3df2 60%,#7a0070);box-shadow:0 0 16px #ff3df2}
.lever.pull{transform:rotate(180deg)}
@keyframes shake{0%{transform:translateY(-5px)}50%{transform:translateY(5px)}100%{transform:translateY(-5px)}}
@keyframes bounce{0%{transform:scale(1.35)}60%{transform:scale(.9)}100%{transform:scale(1)}}
@keyframes glow{50%{box-shadow:0 0 70px #ffe14d,0 0 35px #ff3df2}}
.wwrap{position:relative;width:220px;height:230px;margin:6px auto}
.wheel{position:absolute;top:10px;width:220px;height:220px;border-radius:50%;border:6px solid #b44cff;background:repeating-conic-gradient(#c01040 0 9.73deg,#150a28 9.73deg 19.46deg);transition:transform 3s cubic-bezier(.1,.7,.1,1);box-shadow:0 0 30px #b44cff88}
.hub{position:absolute;top:70px;left:70px;width:80px;height:80px;border-radius:50%;background:#0b0618;border:3px solid #b44cff;display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:900}
.ptr{position:absolute;top:-6px;left:0;right:0;text-align:center;font-size:26px;color:#ffe14d;text-shadow:0 0 10px #ffe14d}
.dice{display:flex;justify-content:center;gap:20px;font-size:100px;line-height:1;margin:10px 0}
.die.roll{animation:roll .5s infinite linear}@keyframes roll{to{transform:rotate(360deg)}}
.scene{perspective:600px;width:130px;height:130px;margin:10px auto}
.coin{width:100%;height:100%;position:relative;transform-style:preserve-3d;transition:transform 1.6s ease-out}
.face{position:absolute;inset:0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:60px;backface-visibility:hidden;-webkit-backface-visibility:hidden;background:radial-gradient(#ffe97a,#d9a400);border:5px solid #fff4;box-shadow:0 0 25px #ffd54d88}
.face.b{transform:rotateY(180deg)}
.hand{display:flex;gap:8px;min-height:92px;flex-wrap:wrap;margin:8px 0}
.pc{width:58px;height:88px;border-radius:10px;background:#fff;color:#111;font-weight:800;font-size:21px;display:flex;align-items:center;justify-content:center;animation:deal .35s;box-shadow:0 0 12px #b44cff88}
.pc.r{color:#d11}.pc.h{background:repeating-linear-gradient(45deg,#7a2cff,#7a2cff 6px,#3b1470 6px,#3b1470 12px);color:#0000}
@keyframes deal{from{transform:translateY(-40px) rotate(-15deg);opacity:0}}
#toast{position:fixed;left:50%;top:42%;transform:translate(-50%,-50%) scale(0);font-size:32px;font-weight:900;padding:16px 30px;border-radius:20px;background:#150a30ee;border:2px solid;z-index:10;pointer-events:none;transition:transform .25s cubic-bezier(.3,1.6,.5,1)}
#toast.show{transform:translate(-50%,-50%) scale(1)}
#toast.w{color:#7dffb0;border-color:#7dffb0;box-shadow:0 0 35px #7dffb0aa}
#toast.l{color:#ff6b8a;border-color:#ff6b8a;box-shadow:0 0 35px #ff6b8aaa}
</style></head><body>
<header><div class="logo">NEON CASINO</div><div class="pill">🪙 <span id="bal">1000</span></div></header>
<main><div class="chips" id="chips"></div><div id="screen"></div></main>
<nav id="nav"></nav><div id="toast"></div>
<script>
const $=s=>document.querySelector(s),sleep=ms=>new Promise(r=>setTimeout(r,ms));
const pid=localStorage.pid||(localStorage.pid=Math.random().toString(36).slice(2));
let bal=1000,bet=50,tab='slots',busy=false,bjS=null,wrot=0,crot=0;
const P={rk:'red',dp:'low',cp:'eagle'},S=['🍒','🍋','🔔','⭐','💎','7️⃣'],F='⚀⚁⚂⚃⚄⚅';
const T={slots:['🎰','Слоти'],roulette:['🎡','Рулетка'],dice:['🎲','Кості'],coin:['🪙','Монетка'],bj:['🃏','21']};
async function api(p,b={}){const r=await fetch('/api/'+p,{method:'POST',headers:{'X-Player':pid},body:JSON.stringify(b)});return r.json()}
function setBal(n){const el=$('#bal'),from=bal,t0=performance.now();bal=n;(function f(t){const k=Math.min(1,(t-t0)/600);el.textContent=Math.round(from+(n-from)*k);if(k<1)requestAnimationFrame(f)})(t0)}
function toast(t,w){const e=$('#toast');e.textContent=t;e.className=(w?'w':'l')+' show';setTimeout(()=>e.classList.remove('show'),1300)}
async function bet_(g,b={}){if(busy)return null;busy=true;const d=await api(g,{bet,...b});if(d.error){busy=false;toast(d.error,0);return null}return d}
async function finish(d){busy=false;setBal(d.balance);const pr=d.win-d.bet;toast(pr>0?'+'+pr+' 🔥':pr==0?'Нічия 🤝':'−'+d.bet,pr>=0);
 if(d.balance<10){await sleep(1800);const r=await api('reset');setBal(r.balance);toast('Бонус 1000 🎁',1)}}
function chips(){$('#chips').innerHTML=[10,50,100,500].map(v=>`<button class="chip ${v==bet?'on':''}" onclick="bet=${v};chips()">${v}</button>`).join('')}
function nav(){$('#nav').innerHTML=Object.entries(T).map(([k,v])=>`<button class="${k==tab?'on':''}" onclick="go('${k}')"><span>${v[0]}</span>${v[1]}</button>`).join('')}
function go(t){if(busy)return;tab=t;nav();$('#screen').innerHTML=V[t]()}
function pick(k,v,el){P[k]=v;el.parentNode.querySelectorAll('.opt').forEach(b=>b.classList.remove('on'));el.classList.add('on')}
const opts=(k,l)=>`<div class="opts">${l.map(([v,t])=>`<button class="opt ${P[k]==v?'on':''}" onclick="pick('${k}','${v}',this)">${t}</button>`).join('')}</div>`;
const V={
slots:()=>`<div class="box"><h2>Слоти</h2><div class="machine" id="mach"><div class="reels"><div class="reel">🍒</div><div class="reel">💎</div><div class="reel">7️⃣</div></div><div class="lever" id="lever" onclick="spin()"><div class="stick"></div><div class="ball"></div></div></div><p class="hint">Потягни за ручку 👉</p></div>`,
roulette:()=>`<div class="box"><h2>Рулетка</h2><div class="wwrap"><div class="ptr">▼</div><div class="wheel" id="wheel"></div><div class="hub" id="hub">?</div></div>${opts('rk',[['red','🔴'],['black','⚫'],['zero','🟢 0'],['num','🔢']])}<input type="number" id="rn" min="0" max="36" value="7" placeholder="Число 0–36 (для 🔢)"><button class="btn" onclick="roul()">КРУТИТИ</button></div>`,
dice:()=>`<div class="box"><h2>Кості</h2><div class="dice"><span class="die">⚃</span><span class="die">⚂</span></div><p class="hint" id="dsum">Сума більше чи менше 7 · x2</p>${opts('dp',[['low','⬇️ Менше 7'],['high','⬆️ Більше 7']])}<button class="btn" onclick="dice()">КИНУТИ</button></div>`,
coin:()=>`<div class="box"><h2>Монетка</h2><div class="scene"><div class="coin" id="coin" style="transform:rotateY(${crot}deg)"><div class="face">🦅</div><div class="face b">🔢</div></div></div>${opts('cp',[['eagle','🦅 Орел'],['tails','🔢 Решка']])}<button class="btn" onclick="coin()">ПІДКИНУТИ</button></div>`,
bj:()=>{const s=bjS,c=h=>h.map(x=>`<div class="pc ${x=='?'?'h':'♥♦'.includes(x.slice(-1))?'r':''}">${x}</div>`).join('');
 let r=`<div class="box"><h2>Блекджек</h2>`;
 if(s){r+=`<div>Дилер ${s.dv!==null?'('+s.dv+')':''}</div><div class="hand">${c(s.dealer)}</div><div>Ти (${s.pv})</div><div class="hand">${c(s.player)}</div>`;
  if(s.done)r+=`<p class="hint">${s.pv>21?'Перебір 💥':s.win>s.bet?'Ти виграв! 🎉':s.win==s.bet?'Нічия':'Дилер виграв'}</p>`}
 else r+=`<p class="hint">Набери 21 і не більше. Блекджек платить x2.5</p>`;
 r+=(!s||s.done)?`<button class="btn" onclick="bj('deal')">РОЗДАТИ</button>`:`<div class="row"><button class="btn" onclick="bj('hit')">➕ ЩЕ</button><button class="btn" onclick="bj('stand')">✋ СТОП</button></div>`;
 return r+'</div>'}};
async function spin(){if(busy)return;const L=$('#lever');L.classList.add('pull');setTimeout(()=>L.classList.remove('pull'),450);
 const d=await bet_('slots');if(!d)return;const R=[...document.querySelectorAll('.reel')];R.forEach(r=>r.classList.add('spin'));
 const iv=setInterval(()=>R.forEach(r=>{if(r.classList.contains('spin'))r.textContent=S[Math.random()*6|0]}),80);
 for(let i=0;i<3;i++){await sleep(800+i*500);R[i].classList.remove('spin','stop');R[i].textContent=d.reels[i];void R[i].offsetWidth;R[i].classList.add('stop')}
 clearInterval(iv);if(d.win>d.bet){const m=$('#mach');m.classList.add('win');setTimeout(()=>m.classList.remove('win'),2200)}finish(d)}
async function roul(){const d=await bet_('roulette',{kind:P.rk,num:+$('#rn').value});if(!d)return;
 wrot+=(1440+Math.random()*360)|0;$('#wheel').style.transform=`rotate(${wrot}deg)`;$('#hub').textContent='…';$('#hub').style.color='#fff';
 await sleep(3100);$('#hub').textContent=d.n;$('#hub').style.color={green:'#3dff8a',red:'#ff4d6d',black:'#fff'}[d.color];finish(d)}
async function dice(){const d=await bet_('dice',{pick:P.dp});if(!d)return;const D=[...document.querySelectorAll('.die')];D.forEach(x=>x.classList.add('roll'));
 const iv=setInterval(()=>D.forEach(x=>x.textContent=F[Math.random()*6|0]),90);await sleep(1100);clearInterval(iv);
 D.forEach((x,i)=>{x.classList.remove('roll');x.textContent=F[d.dice[i]-1]});$('#dsum').textContent='Сума: '+(d.dice[0]+d.dice[1]);finish(d)}
async function coin(){const d=await bet_('coin',{pick:P.cp});if(!d)return;crot=(Math.floor(crot/360)+5)*360+(d.result=='tails'?180:0);
 $('#coin').style.transform=`rotateY(${crot}deg)`;await sleep(1700);finish(d)}
async function bj(a){const d=await bet_('bj'+a);if(!d)return;bjS=d;$('#screen').innerHTML=V.bj();if(d.done)finish(d);else{busy=false;setBal(d.balance)}}
api('state').then(d=>{bal=d.balance;$('#bal').textContent=bal});chips();go('slots');
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(HTML.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            out = play(self.headers.get("X-Player", "anon"), self.path.split("/")[-1], body)
        except Exception as e:
            out = {"error": f"Помилка: {e}"}
        self._send(json.dumps(out).encode(), "application/json")

    def log_message(self, *a):
        pass


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    print(f"\n🎰 NEON CASINO запущено!\n   На телефоні (та сама Wi-Fi): http://{local_ip()}:{PORT}\n   На ПК: http://localhost:{PORT}\n   Зупинити: Ctrl+C\n")
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()