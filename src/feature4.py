import streamlit as st
import pandas as pd
from collections import deque

# DFA CLASS

class DFA:
    def __init__(
        self,
        states,
        alphabet,
        transitions,
        start,
        accept
    ):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions
        self.start = start
        self.accept = set(accept)

    def transition(self, state, symbol):
        return self.transitions.get(
            state,
            {}
        ).get(symbol)

    def accepts(self, string):
        current = self.start

        for symbol in string:

            if symbol not in self.alphabet:
                return False

            current = self.transition(
                current,
                symbol
            )

            if current is None:
                return False

        return current in self.accept

# EQUIVALENCE CHECK

def check_equivalence(dfa1, dfa2):

    alphabet = (
        dfa1.alphabet |
        dfa2.alphabet
    )

    start_pair = (
        dfa1.start,
        dfa2.start
    )

    visited = {start_pair}
    visited_pairs = [start_pair]

    queue = deque()
    queue.append(
        (start_pair, "")
    )

    while queue:

        (
            (q1, q2),
            path
        ) = queue.popleft()

        accept1 = (
            q1 in dfa1.accept
        )

        accept2 = (
            q2 in dfa2.accept
        )

        if accept1 != accept2:

            return (
                False,
                path,
                visited_pairs
            )

        for symbol in sorted(alphabet):

            next_q1 = (
                dfa1.transition(
                    q1,
                    symbol
                )
                if q1 is not None
                else None
            )

            next_q2 = (
                dfa2.transition(
                    q2,
                    symbol
                )
                if q2 is not None
                else None
            )

            next_pair = (
                next_q1,
                next_q2
            )

            if next_pair not in visited:

                visited.add(
                    next_pair
                )

                visited_pairs.append(
                    next_pair
                )

                queue.append(
                    (
                        next_pair,
                        path + symbol
                    )
                )

    return (
        True,
        None,
        visited_pairs
    )

# BUILD DFA

def build_dfa(
    states,
    alphabet,
    transitions,
    start_state,
    accept_states
):
    return DFA(
        states,
        alphabet,
        transitions,
        start_state,
        accept_states
    )

# TABLE VIEW

def create_transition_table(
    states,
    alphabet,
    transitions,
    start_state,
    accept_states
):

    rows = []

    for state in states:

        label = ""

        if state == start_state:
            label += "→ "

        if state in accept_states:
            label += "* "

        label += state

        row = {
            "State": label
        }

        for symbol in alphabet:

            row[symbol] = (
                transitions
                .get(state, {})
                .get(symbol, "-")
            )

        rows.append(row)

    return rows

# SESSION STATE INIT

def initialize_dfa_table(
    prefix,
    states,
    alphabet
):

    st.session_state[
        f"{prefix}_table"
    ] = pd.DataFrame(
        {
            sym: [""] * len(states)
            for sym in alphabet
        },
        index=states
    )

# MAIN PAGE

def show():

    st.header("4. Ekuivalensi Dua DFA")

    st.write(
        "Masukkan dua DFA, kemudian periksa "
        "apakah keduanya menerima bahasa "
        "yang sama (ekuivalen)."
    )

    st.info(
        "Program menggunakan algoritma "
        "Product Automaton + BFS untuk "
        "mencari witness string pembeda."
    )

    with st.expander(
        "Panduan Pengisian DFA"
    ):

        st.markdown("""
### Cara Pengisian

1. Isi daftar state dipisahkan koma.
2. Isi alfabet dipisahkan koma.
3. Isi start state.
4. Isi final state dipisahkan koma.
5. Klik **Buat/Reset Tabel**.
6. Isi fungsi transisi DFA.
7. Klik **Cek Ekuivalensi**.

Contoh:

- States : `q0,q1`
- Alphabet : `a,b`
- Start State : `q0`
- Final States : `q0`
""")

    # INPUT DFA 1

    st.subheader("DFA 1")

    col1, col2 = st.columns(2)

    with col1:

        states1_input = st.text_input(
            "States DFA 1",
            value="q0,q1",
            key="states1"
        )

        start1 = st.text_input(
            "Start State DFA 1",
            value="q0",
            key="start1"
        )

    with col2:

        alphabet1_input = st.text_input(
            "Input DFA 1",
            value="a,b",
            key="alphabet1"
        )

        accept1_input = st.text_input(
            "Final States DFA 1",
            value="q0",
            key="accept1"
        )

    states1 = [
        s.strip()
        for s in states1_input.split(",")
        if s.strip()
    ]

    alphabet1 = [
        a.strip()
        for a in alphabet1_input.split(",")
        if a.strip()
    ]

    accept1 = [
        s.strip()
        for s in accept1_input.split(",")
        if s.strip()
    ]

    if st.button(
        "Buat/Reset Tabel DFA 1"
    ):

        initialize_dfa_table(
            "dfa1",
            states1,
            alphabet1
        )

    if "dfa1_table" not in st.session_state:

        initialize_dfa_table(
            "dfa1",
            states1,
            alphabet1
        )

    st.markdown(
        "**Tabel Transisi DFA 1**"
    )

    dfa1_editor = st.data_editor(
        st.session_state["dfa1_table"],
        use_container_width=True,
        key="dfa1_editor"
    )

    st.divider()

    # INPUT DFA 2

    st.subheader("DFA 2")

    col1, col2 = st.columns(2)

    with col1:

        states2_input = st.text_input(
            "States DFA 2",
            value="even,odd",
            key="states2"
        )

        start2 = st.text_input(
            "Start State DFA 2",
            value="even",
            key="start2"
        )

    with col2:

        alphabet2_input = st.text_input(
            "Input DFA 2",
            value="a,b",
            key="alphabet2"
        )

        accept2_input = st.text_input(
            "Final States DFA 2",
            value="even",
            key="accept2"
        )

    states2 = [
        s.strip()
        for s in states2_input.split(",")
        if s.strip()
    ]

    alphabet2 = [
        a.strip()
        for a in alphabet2_input.split(",")
        if a.strip()
    ]

    accept2 = [
        s.strip()
        for s in accept2_input.split(",")
        if s.strip()
    ]

    if st.button(
        "Buat/Reset Tabel DFA 2"
    ):

        initialize_dfa_table(
            "dfa2",
            states2,
            alphabet2
        )

    if "dfa2_table" not in st.session_state:

        initialize_dfa_table(
            "dfa2",
            states2,
            alphabet2
        )

    st.markdown(
        "**Tabel Transisi DFA 2**"
    )

    dfa2_editor = st.data_editor(
        st.session_state["dfa2_table"],
        use_container_width=True,
        key="dfa2_editor"
    )

    st.divider() 

    # CEK EKUIVALENSI

    if st.button(
        "Cek Ekuivalensi",
        type="primary"
    ):

        errors = []

        # VALIDASI DFA 1

        if not states1:
            errors.append(
                "States DFA 1 tidak boleh kosong."
            )

        if not alphabet1:
            errors.append(
                "Input DFA 1 tidak boleh kosong."
            )

        if start1 not in states1:
            errors.append(
                f"Start state DFA 1 '{start1}' tidak ada pada states."
            )

        for s in accept1:
            if s not in states1:
                errors.append(
                    f"Final state DFA 1 '{s}' tidak ada pada states."
                )

        # VALIDASI DFA 2

        if not states2:
            errors.append(
                "States DFA 2 tidak boleh kosong."
            )

        if not alphabet2:
            errors.append(
                "Input DFA 2 tidak boleh kosong."
            )

        if start2 not in states2:
            errors.append(
                f"Start state DFA 2 '{start2}' tidak ada pada states."
            )

        for s in accept2:
            if s not in states2:
                errors.append(
                    f"Final state DFA 2 '{s}' tidak ada pada states."
                )

        # BANGUN TRANSISI DFA 1

        transitions1 = {}

        for state in states1:

            transitions1[state] = {}

            for symbol in alphabet1:

                try:
                    target = str(
                        dfa1_editor.loc[
                            state,
                            symbol
                        ]
                    ).strip()

                except Exception:
                    target = ""

                if (
                    target
                    and target != "nan"
                ):
                    transitions1[state][
                        symbol
                    ] = target

        # BANGUN TRANSISI DFA 2

        transitions2 = {}

        for state in states2:

            transitions2[state] = {}

            for symbol in alphabet2:

                try:
                    target = str(
                        dfa2_editor.loc[
                            state,
                            symbol
                        ]
                    ).strip()

                except Exception:
                    target = ""

                if (
                    target
                    and target != "nan"
                ):
                    transitions2[state][
                        symbol
                    ] = target

        # VALIDASI TRANSISI DFA 1

        for state in states1:
            for symbol in alphabet1:

                target = (
                    transitions1
                    .get(state, {})
                    .get(symbol)
                )

                if not target:
                    errors.append(
                        f"δ({state}, {symbol}) pada DFA 1 belum diisi."
                    )

                elif target not in states1:
                    errors.append(
                        f"δ({state}, {symbol}) = {target} tidak ada pada states DFA 1."
                    )

        # VALIDASI TRANSISI DFA 2

        for state in states2:
            for symbol in alphabet2:

                target = (
                    transitions2
                    .get(state, {})
                    .get(symbol)
                )

                if not target:
                    errors.append(
                        f"δ({state}, {symbol}) pada DFA 2 belum diisi."
                    )

                elif target not in states2:
                    errors.append(
                        f"δ({state}, {symbol}) = {target} tidak ada pada states DFA 2."
                    )

        if errors:

            st.error(
                "Input tidak valid."
            )

            for e in errors:
                st.markdown(
                    f"- {e}"
                )

            return

        # BUILD DFA

        dfa1 = build_dfa(
            states1,
            alphabet1,
            transitions1,
            start1,
            accept1
        )

        dfa2 = build_dfa(
            states2,
            alphabet2,
            transitions2,
            start2,
            accept2
        )

        st.success(
            "Kedua DFA berhasil dibuat."
        )

        # RINGKASAN DFA

        st.subheader(
            "Ringkasan DFA"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                "### DFA 1"
            )

            st.write(
                f"Jumlah State: {len(states1)}"
            )

            st.write(
                f"Input: {', '.join(alphabet1)}"
            )

            st.write(
                f"Start State: {start1}"
            )

            st.write(
                f"Final States: {', '.join(accept1)}"
            )

        with col2:

            st.markdown(
                "### DFA 2"
            )

            st.write(
                f"Jumlah State: {len(states2)}"
            )

            st.write(
                f"Alphabet: {', '.join(alphabet2)}"
            )

            st.write(
                f"Start State: {start2}"
            )

            st.write(
                f"Final States: {', '.join(accept2)}"
            )

        # CEK EKUIVALENSI

        (
            is_eq,
            witness,
            visited_pairs
        ) = check_equivalence(
            dfa1,
            dfa2
        )

        st.divider()

        st.subheader(
            "Hasil Ekuivalensi"
        )

        if is_eq:

            st.success(
                "Kedua DFA EKUIVALEN"
            )

            st.write(
                "Tidak ditemukan string yang membedakan kedua DFA."
            )

        else:

            st.error(
                "Kedua DFA TIDAK EKUIVALEN"
            )

            if witness == "":
                witness = "ε"

            st.markdown(
                f"### Witness String\n`{witness}`"
            )

            st.write(
                "Witness adalah string terpendek yang menghasilkan keputusan berbeda pada kedua DFA."
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "DFA 1",
                    "DITERIMA"
                    if dfa1.accepts(
                        witness
                        if witness != "ε"
                        else ""
                    )
                    else "DITOLAK"
                )

            with col2:

                st.metric(
                    "DFA 2",
                    "DITERIMA"
                    if dfa2.accepts(
                        witness
                        if witness != "ε"
                        else ""
                    )
                    else "DITOLAK"
                )

        # PRODUCT STATES

        with st.expander(
            "Detail Product States yang Dikunjungi (BFS)"
        ):

            rows = []

            for q1, q2 in visited_pairs:

                rows.append({
                    "State DFA 1": str(q1),
                    "Final DFA 1":
                        "✅"
                        if q1 in dfa1.accept
                        else "—",
                    "State DFA 2": str(q2),
                    "Final DFA 2":
                        "✅"
                        if q2 in dfa2.accept
                        else "—"
                })

            st.table(rows)

            st.caption(
                f"Total pasangan state yang dikunjungi: {len(visited_pairs)}"
            )

        # PENJELASAN

        with st.expander(
            "Penjelasan Algoritma"
        ):

            st.markdown("""
### Product Automaton + BFS

1. Bentuk pasangan state `(q1,q2)` dari DFA1 × DFA2.
2. Mulai dari pasangan state awal.
3. Jelajahi seluruh pasangan state menggunakan BFS.
4. Jika ditemukan pasangan state dengan status final berbeda, DFA tidak ekuivalen.
5. String yang membawa BFS ke pasangan tersebut disebut witness string.
6. Jika BFS selesai tanpa menemukan perbedaan, DFA ekuivalen.

### Kompleksitas Waktu

O(|Q1| × |Q2| × |Σ|)

dengan:

- |Q1| = jumlah state DFA 1
- |Q2| = jumlah state DFA 2
- |Σ| = jumlah simbol alfabet

Setiap pasangan state hanya dikunjungi satu kali oleh BFS.
""")
