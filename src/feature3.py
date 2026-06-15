import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import streamlit as st
import pandas as pd
from itertools import combinations


def draw_dfa(states, transitions, start_state, accept_states, title="DFA"):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title(title, fontsize=13, fontweight='bold', pad=10)

    n = len(states)
    angles = [2 * np.pi * i / n for i in range(n)]
    cx, cy, r = 5, 3.5, 2.5
    pos = {s: (cx + r * np.cos(a - np.pi/2), cy + r * np.sin(a - np.pi/2)) for s, a in zip(states, angles)}

    drawn = {}
    for state in states:
        for symbol, target in transitions.get(state, {}).items():
            if target not in pos:
                continue
            x1, y1 = pos[state]
            x2, y2 = pos[target]
            key = (state, target)
            rev = (target, state)

            if state == target:
                ax.annotate('', xy=(x1+0.35, y1+0.35), xytext=(x1-0.35, y1+0.35),
                            arrowprops=dict(arrowstyle='->', color='gray',
                                           connectionstyle='arc3,rad=-2.5', lw=1.2))
                ax.text(x1, y1+1.0, symbol, ha='center', fontsize=8, color='gray')
            else:
                rad = 0.25 if rev in drawn else 0.0
                ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                            arrowprops=dict(arrowstyle='->', color='gray',
                                           connectionstyle=f'arc3,rad={rad}', lw=1.2))
                mx = (x1+x2)/2 + rad*(y2-y1)*0.4
                my = (y1+y2)/2 - rad*(x2-x1)*0.4
                existing = drawn.get(key, '')
                drawn[key] = (existing+','+symbol).strip(',')
                ax.text(mx, my, drawn[key], ha='center', fontsize=8,
                        bbox=dict(fc='white', ec='none', pad=1), color='#444')
            if key not in drawn:
                drawn[key] = symbol

    for state in states:
        x, y = pos[state]
        color = '#4CAF50' if state in accept_states else '#2196F3'
        ax.add_patch(plt.Circle((x, y), 0.45, color=color, zorder=3, alpha=0.85))
        if state in accept_states:
            ax.add_patch(plt.Circle((x, y), 0.37, fill=False, ec='white', lw=1.2, zorder=4))
        ax.text(x, y, state, ha='center', va='center', fontsize=9,
                fontweight='bold', color='white', zorder=5)
        if state == start_state:
            ax.annotate('', xy=(x-0.45, y), xytext=(x-1.0, y),
                        arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close()
    buf.seek(0)
    return buf


def minimize_dfa(states, alphabet, transitions, start_state, accept_states):
    reachable = set()
    queue = [start_state]
    while queue:
        state = queue.pop(0)
        if state in reachable:
            continue
        reachable.add(state)
        for symbol in alphabet:
            next_state = transitions.get(state, {}).get(symbol)
            if next_state and next_state not in reachable:
                queue.append(next_state)

    states = [s for s in states if s in reachable]
    accept_states = [s for s in accept_states if s in reachable]

    pairs = list(combinations(states, 2))
    distinguished = {(p, q): (p in accept_states) != (q in accept_states) for p, q in pairs}

    changed = True
    while changed:
        changed = False
        for p, q in pairs:
            key = (p, q)
            if distinguished[key]:
                continue
            for symbol in alphabet:
                p_next = transitions.get(p, {}).get(symbol)
                q_next = transitions.get(q, {}).get(symbol)
                if p_next == q_next:
                    continue
                if p_next is None or q_next is None:
                    distinguished[key] = True
                    changed = True
                    break
                pair_check = (p_next, q_next) if (p_next, q_next) in distinguished else (q_next, p_next)
                if distinguished.get(pair_check, False):
                    distinguished[key] = True
                    changed = True
                    break

    parent = {s: s for s in states}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p, q in pairs:
        if not distinguished[(p, q)]:
            parent[find(p)] = find(q)

    groups = {}
    for s in states:
        groups.setdefault(find(s), set()).add(s)
    partitions = list(groups.values())

    def get_partition(state):
        for i, part in enumerate(partitions):
            if state in part:
                return i

    partition_labels = {i: sorted(part)[0] for i, part in enumerate(partitions)}

    def label(state):
        return partition_labels[get_partition(state)]

    new_start = label(start_state)
    new_accept = list(set(label(s) for s in accept_states))
    new_transitions = {}
    for i, part in enumerate(partitions):
        lbl = partition_labels[i]
        rep = next(iter(part))
        new_transitions[lbl] = {}
        for symbol in alphabet:
            next_s = transitions.get(rep, {}).get(symbol)
            if next_s:
                new_transitions[lbl][symbol] = label(next_s)

    return {
        "reachable_states": states,
        "partitions": partitions,
        "partition_labels": partition_labels,
        "new_start": new_start,
        "new_accept": new_accept,
        "new_transitions": new_transitions,
    }


def show():
    st.header("3. Minimalisasi DFA")
    st.write("Masukkan DFA untuk diminimalkan menggunakan metode Table Filling.")

    with st.expander("Panduan Pengisian & Contoh DFA"):
        st.markdown("""
        **Cara Pengisian:**
        1. Isi **States** dengan nama-nama state, dipisah koma. Contoh: `A,B,C,D,E`
        2. Isi **Alphabet** dengan simbol input, dipisah koma. Contoh: `0,1`
        3. Isi **Start State** dengan satu state awal. Contoh: `A`
        4. Isi **Accept States** dengan state penerima, dipisah koma. Contoh: `C,D`
        5. Klik **Buat/Reset Tabel Transisi** untuk membuat tabel sesuai input.
        6. Isi tabel transisi — setiap sel diisi dengan state tujuan.
        7. Klik **Minimalisasi DFA** untuk melihat hasil.

        ---

        **Contoh DFA (memiliki state redundant):**

        | State | 0 | 1 |
        |-------|---|---|
        | A     | B | C |
        | B     | A | D |
        | C     | E | F |
        | D     | E | F |
        | E     | E | F |
        | F     | F | F |

        - States: `A,B,C,D,E,F`
        - Alphabet: `0,1`
        - Start State: `A`
        - Accept States: `C,D,E`

        Hasil yang diharapkan: state **C, D, E** akan digabung karena equivalent.
        """)

    col1, col2 = st.columns(2)
    with col1:
        states_input = st.text_input("States (pisah koma)", value="q0,q1,q2,q3,q4", key="states_input")
        start_state = st.text_input("Start State", value="q0", key="start_input")
    with col2:
        alphabet_input = st.text_input("Alphabet (pisah koma)", value="a,b", key="alphabet_input")
        accept_input = st.text_input("Accept States (pisah koma)", value="q3,q4", key="accept_input")

    states = [s.strip() for s in states_input.split(",") if s.strip()]
    alphabet = [a.strip() for a in alphabet_input.split(",") if a.strip()]
    accept_states = [s.strip() for s in accept_input.split(",") if s.strip()]

    st.subheader("Tabel Transisi")

    if st.button("Buat/Reset Tabel Transisi"):
        st.session_state.prev_states = states
        st.session_state.prev_alphabet = alphabet
        st.session_state.transition_df = pd.DataFrame(
            {sym: [""] * len(states) for sym in alphabet}, index=states
        )

    if "transition_df" not in st.session_state:
        st.session_state.prev_states = states
        st.session_state.prev_alphabet = alphabet
        st.session_state.transition_df = pd.DataFrame(
            {sym: [""] * len(states) for sym in alphabet}, index=states
        )

    edited_df = st.data_editor(
        st.session_state.transition_df,
        use_container_width=True,
        key="trans_editor"
    )

    if st.button("Minimalisasi DFA", type="primary"):
        errors = []
        if not states: errors.append("States tidak boleh kosong.")
        if not alphabet: errors.append("Alphabet tidak boleh kosong.")
        if start_state not in states: errors.append(f"Start state '{start_state}' tidak ada di states.")
        for s in accept_states:
            if s not in states: errors.append(f"Accept state '{s}' tidak ada di states.")
        if errors:
            for e in errors: st.error(e)
            return

        transitions = {}
        for state in states:
            transitions[state] = {}
            for symbol in alphabet:
                try:
                    val = str(edited_df.loc[state, symbol]).strip()
                except:
                    val = ""
                if val and val != "nan":
                    transitions[state][symbol] = val

        # Validasi transisi
        errors = []
        warnings = []
        
         # Satu sel transisi tidak boleh berisi lebih dari 1 state (bukan NFA)
        for state in states:
            for symbol in alphabet:
                target = transitions.get(state, {}).get(symbol, "")
                if ',' in target:
                    errors.append(f"δ({state}, {symbol}) = {target} | DFA hanya boleh 1 state tujuan per transisi.")

        # State tujuan tidak ada di himpunan states
        for state in states:
            for symbol in alphabet:
                target = transitions.get(state, {}).get(symbol)
                if target and target not in states:
                    errors.append(f"δ({state}, {symbol}) = {target} | {target} tidak ada di himpunan states.")

        # DFA tidak lengkap, ada state+simbol yang tidak punya transisi
        missing = []
        for state in states:
            for symbol in alphabet:
                if not transitions.get(state, {}).get(symbol):
                    missing.append(f"δ({state}, {symbol})")
        if missing:
            warnings.append(f"Transisi tidak lengkap (akan diabaikan saat minimalisasi): {', '.join(missing)}")

        # Duplikat nama state
        if len(states) != len(set(states)):
            dupes = [s for s in set(states) if states.count(s) > 1]
            errors.append(f"Nama state duplikat: {', '.join(dupes)}")

        # Duplikat simbol alphabet
        if len(alphabet) != len(set(alphabet)):
            dupes = [a for a in set(alphabet) if alphabet.count(a) > 1]
            errors.append(f"Simbol alphabet duplikat: {', '.join(dupes)}")

        # Accept states kosong, warning (DFA valid tapi selalu reject)
        if not accept_states:
            warnings.append("Tidak ada accept state, DFA akan menolak semua string.")

        # Semua state adalah accept state, warning
        if set(accept_states) == set(states):
            warnings.append("Semua state adalah accept state, DFA menerima semua string.")

        for w in warnings:
            st.warning(w)
        if errors:
            st.error("Input tidak valid, perbaiki terlebih dahulu:")
            for e in errors:
                st.markdown(f"- {e}")
            return

        result = minimize_dfa(states, alphabet, transitions, start_state, accept_states)

        st.success("DFA berhasil diminimalkan!")

        # Ilustrasi sebelum & sesudah
        st.subheader("Ilustrasi DFA")
        col1, col2 = st.columns(2)
        with col1:
            st.image(draw_dfa(states, transitions, start_state, accept_states,
                              title="Sebelum Minimalisasi"))
        with col2:
            new_states = list(result["new_transitions"].keys())
            st.image(draw_dfa(new_states, result["new_transitions"],
                              result["new_start"], result["new_accept"],
                              title="Sesudah Minimalisasi"))

        st.subheader("Hasil Minimal DFA")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("State Awal", len(states))
        with col2: st.metric("State Minimal", len(result["partitions"]))
        with col3: st.metric("State Dihapus", len(states) - len(result["partitions"]))

        st.markdown(f"- **Start State:** {result['new_start']}")
        st.markdown(f"- **Accept States:** {', '.join(result['new_accept'])}")

        # Himpunan state yang equivalen
        st.markdown("**Kelompok State Equivalent:**")
        for i, part in enumerate(result["partitions"]):
            lbl = result["partition_labels"][i]
            members = sorted(part)
            if len(members) > 1:
                eliminated = ", ".join(m for m in members if m != lbl)
                st.markdown(f"- **{lbl}** = {{ {', '.join(members)} }} → *{eliminated} dieliminasi, digabung ke {lbl}*")
            else:
                st.markdown(f"- **{lbl}** = {{ {', '.join(members)} }}")

        # Tabel transisi DFA setelah minimalisasi
        st.markdown("**Tabel Transisi Minimal DFA:**")
        rows = [{"State": s, **{sym: t for sym, t in trans.items()}} for s, trans in result["new_transitions"].items()]
        st.dataframe(pd.DataFrame(rows).set_index("State"), use_container_width=True)