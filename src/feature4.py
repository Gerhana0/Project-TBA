import json
from automata.fa.dfa import DFA
from automata.fa.nfa import NFA
import streamlit as st
from collections import deque


CONTOH_DFA_1 = {
    "states": ["q0", "q1"],
    "input_symbols": ["a", "b"],
    "transitions": {
        "q0": {"a": "q1", "b": "q0"},
        "q1": {"a": "q0", "b": "q1"}
    },
    "initial_state": "q0",
    "final_states": ["q0"]
}

CONTOH_DFA_2 = {
    "states": ["even", "odd"],
    "input_symbols": ["a", "b"],
    "transitions": {
        "even": {"a": "odd", "b": "even"},
        "odd": {"a": "even", "b": "odd"}
    },
    "initial_state": "even",
    "final_states": ["even"]
}


class DFA:
    def __init__(self, states, alphabet, transitions, start, accept):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions
        self.start = start
        self.accept = set(accept)

    def transition(self, state, symbol):
        return self.transitions.get(state, {}).get(symbol)

    def accepts(self, string):
        current = self.start

        for symbol in string:
            if symbol not in self.alphabet:
                return False

            current = self.transition(current, symbol)

            if current is None:
                return False

        return current in self.accept


def check_equivalence(dfa1, dfa2):
    alphabet = dfa1.alphabet | dfa2.alphabet

    start_pair = (dfa1.start, dfa2.start)

    visited = {start_pair}
    visited_pairs = [start_pair]

    queue = deque()
    queue.append((start_pair, ""))

    while queue:
        (q1, q2), path = queue.popleft()

        q1_accept = q1 in dfa1.accept
        q2_accept = q2 in dfa2.accept

        if q1_accept != q2_accept:
            return False, path, visited_pairs

        for symbol in sorted(alphabet):
            next_q1 = (
                dfa1.transition(q1, symbol)
                if q1 is not None
                else None
            )

            next_q2 = (
                dfa2.transition(q2, symbol)
                if q2 is not None
                else None
            )

            next_pair = (next_q1, next_q2)

            if next_pair not in visited:
                visited.add(next_pair)
                visited_pairs.append(next_pair)
                queue.append((next_pair, path + symbol))

    return True, None, visited_pairs


def build_dfa_from_json(data):
    return DFA(
        states=data["states"],
        alphabet=data["input_symbols"],
        transitions=data["transitions"],
        start=data["initial_state"],
        accept=data["final_states"]
    )


def show():
    st.header("4. Ekuivalensi Dua DFA")

    st.write(
        "Masukkan dua DFA dalam format JSON, lalu cek apakah "
        "keduanya menerima bahasa yang sama."
    )

    with st.expander("Panduan Format JSON & Contoh DFA"):
        st.markdown("""
Format DFA sama seperti pada Feature 1.

Field yang wajib ada:

- `states`
- `input_symbols`
- `transitions`
- `initial_state`
- `final_states`

Dua DFA dikatakan ekuivalen apabila menerima bahasa yang sama.
""")

    col1, col2 = st.columns(2)

    with col1:
        json_dfa1 = st.text_area(
            "DFA 1",
            value=json.dumps(CONTOH_DFA_1, indent=2),
            height=350
        )

    with col2:
        json_dfa2 = st.text_area(
            "DFA 2",
            value=json.dumps(CONTOH_DFA_2, indent=2),
            height=350
        )

    if st.button("Cek Ekuivalensi", type="primary"):

        try:
            data1 = json.loads(json_dfa1)
            data2 = json.loads(json_dfa2)

        except json.JSONDecodeError as e:
            st.error(f"Format JSON tidak valid: {e}")
            return

        try:
            dfa1 = build_dfa_from_json(data1)
            dfa2 = build_dfa_from_json(data2)

        except KeyError as e:
            st.error(f"Field wajib tidak ditemukan: {e}")
            return

        is_eq, witness, visited_pairs = check_equivalence(
            dfa1,
            dfa2
        )

        st.divider()
        st.subheader("Hasil")

        if is_eq:
            st.success("✅ Kedua DFA EKUIVALEN")

            st.write(
                "Tidak ditemukan string yang membedakan "
                "kedua DFA."
            )

        else:
            st.error("❌ Kedua DFA TIDAK EKUIVALEN")

            st.markdown(
                f"**Witness (string pembeda):** `{witness}`"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "DFA 1",
                    "DITERIMA"
                    if dfa1.accepts(witness)
                    else "DITOLAK"
                )

            with col2:
                st.metric(
                    "DFA 2",
                    "DITERIMA"
                    if dfa2.accepts(witness)
                    else "DITOLAK"
                )

        with st.expander(
            "Detail Product States yang Dikunjungi (BFS)"
        ):
            rows = []

            for q1, q2 in visited_pairs:
                rows.append({
                    "State DFA 1": str(q1),
                    "Accept DFA 1":
                        "✅" if q1 in dfa1.accept else "—",
                    "State DFA 2": str(q2),
                    "Accept DFA 2":
                        "✅" if q2 in dfa2.accept else "—"
                })

            st.table(rows)

        with st.expander("Penjelasan Algoritma"):
            st.markdown("""
### Product Automaton + BFS

1. Bentuk pasangan state `(q1, q2)` dari DFA1 × DFA2.
2. Mulai dari pasangan state awal.
3. Jelajahi seluruh pasangan state menggunakan BFS.
4. Jika ditemukan pasangan state di mana hanya satu DFA berada pada state penerima, maka kedua DFA tidak ekuivalen.
5. Jika BFS selesai tanpa menemukan kondisi tersebut, kedua DFA ekuivalen.

Kompleksitas:

O(|Q1| × |Q2| × |Σ|)
""")