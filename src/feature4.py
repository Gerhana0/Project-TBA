import streamlit as st
import pandas as pd
import graphviz

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

# DIAGRAM STATE (GRAPHVIZ)

def draw_dfa(dfa, title="DFA"):

    graph = graphviz.Digraph()

    graph.attr(
        rankdir="LR",
        label=title,
        labelloc="t",
        fontsize="16"
    )

    graph.attr(
        "node",
        shape="circle",
        fontsize="12"
    )

    # TITIK INVISIBLE UNTUK PENANDA START STATE

    graph.node(
        "__start__",
        shape="point",
        label=""
    )

    for state in sorted(dfa.states):

        shape = (
            "doublecircle"
            if state in dfa.accept
            else "circle"
        )

        graph.node(
            state,
            shape=shape
        )

    graph.edge(
        "__start__",
        dfa.start
    )

    # KUMPULKAN LABEL TRANSISI YANG MENUJU STATE SAMA

    edge_labels = {}

    for state in sorted(dfa.states):

        for symbol in sorted(dfa.alphabet):

            target = dfa.transition(
                state,
                symbol
            )

            if target is None:
                continue

            key = (state, target)

            if key not in edge_labels:
                edge_labels[key] = []

            edge_labels[key].append(symbol)

    for (src, dst), symbols in edge_labels.items():

        graph.edge(
            src,
            dst,
            label=", ".join(symbols)
        )

    return graph

# TABLE-FILLING METHOD (PRODUCT STATE PAIRS)

def build_equivalence_table(dfa1, dfa2):
    """
    Membangun tabel pasangan state (V, V') beserta hasil
    transisinya untuk setiap simbol pada alfabet gabungan,
    mengikuti pendekatan product automaton table-filling.

    Mengembalikan:
        rows: list of dict, satu baris per pasangan state
              yang dikunjungi, berisi pasangan state saat ini
              dan pasangan state hasil transisi tiap simbol.
        is_equivalent: bool, hasil akhir ekuivalensi
        distinguishing_pair: pasangan state pertama yang
              status final-nya berbeda (None jika ekuivalen)
    """

    alphabet = sorted(
        dfa1.alphabet | dfa2.alphabet
    )

    start_pair = (dfa1.start, dfa2.start)

    visited = [start_pair]
    visited_set = {start_pair}

    rows = []
    is_equivalent = True
    distinguishing_pair = None

    index = 0

    while index < len(visited):

        q1, q2 = visited[index]
        index += 1

        accept1 = q1 in dfa1.accept if q1 is not None else False
        accept2 = q2 in dfa2.accept if q2 is not None else False

        row = {
            "Pasangan State": f"({q1}, {q2})"
        }

        if (
            q1 == dfa1.start
            and q2 == dfa2.start
        ):
            row["Pasangan State"] = "→ " + row["Pasangan State"]

        same_status = (accept1 == accept2)

        if not same_status and is_equivalent:
            is_equivalent = False
            distinguishing_pair = (q1, q2)

        for symbol in alphabet:

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

            row[f"({symbol}, {symbol})"] = (
                f"({next_q1}, {next_q2})"
            )

            if next_pair not in visited_set:
                visited_set.add(next_pair)
                visited.append(next_pair)

        rows.append(row)

    return rows, is_equivalent, distinguishing_pair


def generate_equivalence_explanation(
    dfa1,
    dfa2,
    is_equivalent,
    distinguishing_pair
):
    """
    Menyusun penjelasan kesimpulan secara otomatis
    berdasarkan hasil tabel pasangan state.
    """

    alphabet = sorted(dfa1.alphabet | dfa2.alphabet)

    if is_equivalent:

        explanation = (
            f"∴ DFA 1 dan DFA 2 **EKUIVALEN**, karena setiap "
            f"pasangan state yang dikunjungi, saat diberi input "
            f"{', '.join(alphabet)}, selalu menuju ke pasangan "
            f"state dengan status yang sama (sama-sama final "
            f"state atau sama-sama non-final state). Tidak "
            f"ditemukan pasangan state dengan status final yang "
            f"berbeda, sehingga kedua DFA menerima bahasa yang "
            f"sama."
        )

    else:

        q1, q2 = distinguishing_pair

        status1 = (
            "final state"
            if q1 in dfa1.accept
            else "non-final state"
        )

        status2 = (
            "final state"
            if q2 in dfa2.accept
            else "non-final state"
        )

        explanation = (
            f"∴ DFA 1 dan DFA 2 **TIDAK EKUIVALEN**, karena pada "
            f"pasangan state ({q1}, {q2}), state {q1} pada DFA 1 "
            f"merupakan {status1} sedangkan state {q2} pada "
            f"DFA 2 merupakan {status2}. Karena status final "
            f"keduanya berbeda, maka terdapat string yang "
            f"menghasilkan keputusan berbeda pada kedua DFA, "
            f"sehingga kedua DFA tidak menerima bahasa yang sama."
        )

    return explanation

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

        # RINGKASAN DFA + DIAGRAM STATE

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

            st.graphviz_chart(
                draw_dfa(dfa1, "DFA 1")
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

            st.graphviz_chart(
                draw_dfa(dfa2, "DFA 2")
            )

        # CEK EKUIVALENSI (TABLE-FILLING METHOD)

        (
            table_rows,
            is_eq,
            distinguishing_pair
        ) = build_equivalence_table(
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

        else:

            st.error(
                "Kedua DFA TIDAK EKUIVALEN"
            )

        st.markdown(
            "**Tabel Pasangan State**"
        )

        st.table(
            pd.DataFrame(table_rows)
        )

        explanation = generate_equivalence_explanation(
            dfa1,
            dfa2,
            is_eq,
            distinguishing_pair
        )

        st.markdown(explanation)