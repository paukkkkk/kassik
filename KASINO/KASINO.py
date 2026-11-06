import random
import streamlit as st

st.set_page_config(page_title="Казино для прикола", page_icon="🎰", layout="centered")

START_BALANCE = 1000
RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

# ---------- стан ----------
if "balance" not in st.session_state:
    st.session_state.balance = START_BALANCE
    st.session_state.bj = None


def pay(amount):
    st.session_state.balance += int(amount)


def show_result(won, text):
    (st.success if won else st.error)(text)


# ---------- шапка ----------
st.title("🎰 Казино «Для прикола»")
st.caption("Гроші віртуальні, все чисто для сміху 😄")
balance_box = st.empty()

if st.session_state.balance < 10:
    st.warning("Ти все програв 💸")
    if st.button("🔄 Почати знову", use_container_width=True):
        st.session_state.balance = START_BALANCE
        st.session_state.bj = None
        st.rerun()
    balance_box.metric("Баланс", f"{st.session_state.balance} 🪙")
    st.stop()

bet = st.number_input(
    "Ставка 🪙",
    min_value=10,
    max_value=max(10, st.session_state.balance),
    value=min(100, st.session_state.balance),
    step=10,
)

tabs = st.tabs(["🎰 Слоти", "🎡 Рулетка", "🎲 Кості", "🪙 Монетка", "🃏 Блекджек"])

# ---------- СЛОТИ ----------
with tabs[0]:
    st.subheader("Слоти")
    st.write("3 однакові — виграш x10 (💎 x25, 7️⃣ x50). 2 однакові — x1.5.")
    if st.button("Крутити 🎰", use_container_width=True, key="slots"):
        pay(-bet)
        symbols = ["🍒", "🍋", "🔔", "⭐", "💎", "7️⃣"]
        weights = [30, 25, 20, 15, 7, 3]
        reels = random.choices(symbols, weights=weights, k=3)
        st.markdown(f"<h1 style='text-align:center'>{' '.join(reels)}</h1>", unsafe_allow_html=True)
        if len(set(reels)) == 1:
            mult = {"7️⃣": 50, "💎": 25}.get(reels[0], 10)
            pay(bet * mult)
            show_result(True, f"ДЖЕКПОТ! x{mult} → +{bet * mult - bet} 🪙")
        elif len(set(reels)) == 2:
            pay(bet * 1.5)
            show_result(True, f"Дві однакові! +{int(bet * 0.5)} 🪙")
        else:
            show_result(False, f"Мимо... -{bet} 🪙")

# ---------- РУЛЕТКА ----------
with tabs[1]:
    st.subheader("Рулетка")
    kind = st.radio("На що ставиш?", ["🔴 Червоне", "⚫ Чорне", "🟢 Зеро", "🔢 Число"], horizontal=True)
    number = None
    if kind == "🔢 Число":
        number = st.number_input("Число (0–36)", 0, 36, 7)
    if st.button("Крутити рулетку 🎡", use_container_width=True, key="roulette"):
        pay(-bet)
        n = random.randint(0, 36)
        color = "🟢" if n == 0 else ("🔴" if n in RED else "⚫")
        st.markdown(f"<h1 style='text-align:center'>{color} {n}</h1>", unsafe_allow_html=True)
        win_mult = 0
        if kind == "🔴 Червоне" and n in RED:
            win_mult = 2
        elif kind == "⚫ Чорне" and n != 0 and n not in RED:
            win_mult = 2
        elif kind == "🟢 Зеро" and n == 0:
            win_mult = 36
        elif kind == "🔢 Число" and n == number:
            win_mult = 36
        if win_mult:
            pay(bet * win_mult)
            show_result(True, f"Виграш x{win_mult}! +{bet * win_mult - bet} 🪙")
        else:
            show_result(False, f"Не пощастило. -{bet} 🪙")

# ---------- КОСТІ ----------
with tabs[2]:
    st.subheader("Кості")
    st.write("Кидаємо дві кубики. Ставиш на сума більше чи менше 7. Рівно 7 — програш. Виграш x2.")
    choice = st.radio("Твій вибір", ["⬇️ Менше 7", "⬆️ Більше 7"], horizontal=True)
    if st.button("Кинути 🎲", use_container_width=True, key="dice"):
        pay(-bet)
        a, b = random.randint(1, 6), random.randint(1, 6)
        total = a + b
        st.markdown(f"<h1 style='text-align:center'>🎲 {a} + {b} = {total}</h1>", unsafe_allow_html=True)
        won = (choice.startswith("⬇️") and total < 7) or (choice.startswith("⬆️") and total > 7)
        if won:
            pay(bet * 2)
            show_result(True, f"Є! +{bet} 🪙")
        else:
            show_result(False, f"Ні! -{bet} 🪙")

# ---------- МОНЕТКА ----------
with tabs[3]:
    st.subheader("Монетка")
    side = st.radio("Обираєш", ["🦅 Орел", "🔢 Решка"], horizontal=True)
    if st.button("Підкинути 🪙", use_container_width=True, key="coin"):
        pay(-bet)
        result = random.choice(["🦅 Орел", "🔢 Решка"])
        st.markdown(f"<h1 style='text-align:center'>{result}</h1>", unsafe_allow_html=True)
        if result == side:
            pay(bet * 2)
            show_result(True, f"Вгадав! +{bet} 🪙")
        else:
            show_result(False, f"Не вгадав. -{bet} 🪙")

# ---------- БЛЕКДЖЕК ----------
CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def hand_value(hand):
    total, aces = 0, 0
    for c in hand:
        if c == "A":
            total += 11
            aces += 1
        elif c in ("10", "J", "Q", "K"):
            total += 10
        else:
            total += int(c)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def finish_bj():
    g = st.session_state.bj
    p = hand_value(g["player"])
    if p <= 21:
        while hand_value(g["dealer"]) < 17:
            g["dealer"].append(random.choice(CARDS))
    d = hand_value(g["dealer"])
    natural = p == 21 and len(g["player"]) == 2
    if p > 21:
        g["result"], g["won"], payout = f"Перебір! -{g['bet']} 🪙", False, 0
    elif natural and not (d == 21 and len(g["dealer"]) == 2):
        payout = int(g["bet"] * 2.5)
        g["result"], g["won"] = f"БЛЕКДЖЕК! +{payout - g['bet']} 🪙", True
    elif d > 21 or p > d:
        payout = g["bet"] * 2
        g["result"], g["won"] = f"Ти виграв! +{g['bet']} 🪙", True
    elif p == d:
        payout = g["bet"]
        g["result"], g["won"] = "Нічия, ставку повернуто", True
    else:
        g["result"], g["won"], payout = f"Дилер виграв. -{g['bet']} 🪙", False, 0
    pay(payout)
    g["done"] = True


with tabs[4]:
    st.subheader("Блекджек")
    g = st.session_state.bj

    if g is None or g["done"]:
        if st.button("Роздати карти 🃏", use_container_width=True, key="deal"):
            pay(-bet)
            st.session_state.bj = {
                "player": [random.choice(CARDS), random.choice(CARDS)],
                "dealer": [random.choice(CARDS), random.choice(CARDS)],
                "bet": bet,
                "done": False,
                "result": "",
                "won": False,
            }
            if hand_value(st.session_state.bj["player"]) == 21:
                finish_bj()
            st.rerun()
    else:
        c1, c2 = st.columns(2)
        if c1.button("➕ Ще карту", use_container_width=True, key="hit"):
            g["player"].append(random.choice(CARDS))
            if hand_value(g["player"]) >= 21:
                finish_bj()
            st.rerun()
        if c2.button("✋ Стоп", use_container_width=True, key="stand"):
            finish_bj()
            st.rerun()

    g = st.session_state.bj
    if g:
        st.write(f"**Твої карти** ({hand_value(g['player'])}):  " + "  ".join(f"`{c}`" for c in g["player"]))
        if g["done"]:
            st.write(f"**Дилер** ({hand_value(g['dealer'])}):  " + "  ".join(f"`{c}`" for c in g["dealer"]))
            show_result(g["won"], g["result"])
        else:
            st.write(f"**Дилер:**  `{g['dealer'][0]}`  `?`")

# ---------- баланс (оновлюється в кінці) ----------
balance_box.metric("Баланс", f"{st.session_state.balance} 🪙")