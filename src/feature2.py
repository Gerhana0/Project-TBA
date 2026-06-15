import streamlit as st
import re
import graphviz
from automata.fa.nfa import NFA

class ThompsonNFA:
    def __init__(self):
        self._state_counter = 0

    def _new_state(self) -> str:
        s = f"q{self._state_counter}"
        self._state_counter += 1
        return s

    def _epsilon_nfa(self) -> dict:
        """NFA yang menerima hanya string kosong (ε)."""
        start = self._new_state()
        accept = self._new_state()
        return {
            "states": {start, accept},
            "start": start,
            "accept": accept,
            "transitions": {start: {"": {accept}}},
        }

    def _symbol_nfa(self, symbol: str) -> dict:
        """NFA yang menerima tepat satu simbol."""
        start = self._new_state()
        accept = self._new_state()
        return {
            "states": {start, accept},
            "start": start,
            "accept": accept,
            "transitions": {start: {symbol: {accept}}},
        }

    def _concat(self, nfa1: dict, nfa2: dict) -> dict:
        """Konkatenasi dua NFA."""
        # Gabungkan: final state nfa1 → ε → start state nfa2
        transitions = {**nfa1["transitions"]}
        for state, trans in nfa2["transitions"].items():
            if state not in transitions:
                transitions[state] = {}
            for sym, targets in trans.items():
                if sym not in transitions[state]:
                    transitions[state][sym] = set()
                transitions[state][sym] |= targets

        # Tambahkan ε-transition dari accept nfa1 ke start nfa2
        accept1 = nfa1["accept"]
        if accept1 not in transitions:
            transitions[accept1] = {}
        if "" not in transitions[accept1]:
            transitions[accept1][""] = set()
        transitions[accept1][""] |= {nfa2["start"]}

        return {
            "states": nfa1["states"] | nfa2["states"],
            "start": nfa1["start"],
            "accept": nfa2["accept"],
            "transitions": transitions,
        }

    def _union(self, nfa1: dict, nfa2: dict) -> dict:
        """Union (|) dua NFA."""
        new_start = self._new_state()
        new_accept = self._new_state()

        transitions = {}
        # ε dari new_start ke start kedua NFA
        transitions[new_start] = {"": {nfa1["start"], nfa2["start"]}}

        for nfa in [nfa1, nfa2]:
            for state, trans in nfa["transitions"].items():
                if state not in transitions:
                    transitions[state] = {}
                for sym, targets in trans.items():
                    if sym not in transitions[state]:
                        transitions[state][sym] = set()
                    transitions[state][sym] |= targets
            # ε dari accept masing-masing NFA ke new_accept
            old_accept = nfa["accept"]
            if old_accept not in transitions:
                transitions[old_accept] = {}
            if "" not in transitions[old_accept]:
                transitions[old_accept][""] = set()
            transitions[old_accept][""] |= {new_accept}

        return {
            "states": nfa1["states"] | nfa2["states"] | {new_start, new_accept},
            "start": new_start,
            "accept": new_accept,
            "transitions": transitions,
        }

    def _kleene_star(self, nfa: dict) -> dict:
        """Kleene star (*) pada NFA."""
        new_start = self._new_state()
        new_accept = self._new_state()

        transitions = {}
        # ε: new_start → nfa.start dan new_start → new_accept
        transitions[new_start] = {"": {nfa["start"], new_accept}}

        for state, trans in nfa["transitions"].items():
            if state not in transitions:
                transitions[state] = {}
            for sym, targets in trans.items():
                if sym not in transitions[state]:
                    transitions[state][sym] = set()
                transitions[state][sym] |= targets

        # ε: nfa.accept → nfa.start dan nfa.accept → new_accept
        old_accept = nfa["accept"]
        if old_accept not in transitions:
            transitions[old_accept] = {}
        if "" not in transitions[old_accept]:
            transitions[old_accept][""] = set()
        transitions[old_accept][""] |= {nfa["start"], new_accept}

        return {
            "states": nfa["states"] | {new_start, new_accept},
            "start": new_start,
            "accept": new_accept,
            "transitions": transitions,
        }

    def _plus(self, nfa: dict) -> dict:
        """Plus (+): satu atau lebih → concat(nfa, kleene_star(nfa))."""
        # Buat salinan NFA untuk kleene star agar state tidak overlap
        # Kita pakai union pendekatan: NFA+ = NFA · NFA*
        star_part = self._kleene_star(self._copy_nfa(nfa))
        return self._concat(nfa, star_part)

    def _optional(self, nfa: dict) -> dict:
        """Optional (?): nol atau satu → union(nfa, epsilon)."""
        eps = self._epsilon_nfa()
        return self._union(nfa, eps)

    def _copy_nfa(self, nfa: dict) -> dict:
        """Buat salinan NFA dengan state baru agar tidak ada konflik."""
        old_states = sorted(nfa["states"])
        rename = {s: self._new_state() for s in old_states}

        new_transitions = {}
        for state, trans in nfa["transitions"].items():
            ns = rename[state]
            new_transitions[ns] = {}
            for sym, targets in trans.items():
                new_transitions[ns][sym] = {rename[t] for t in targets}

        return {
            "states": set(rename.values()),
            "start": rename[nfa["start"]],
            "accept": rename[nfa["accept"]],
            "transitions": new_transitions,
        }

    # ─── Regex Parser (Recursive Descent) ────────────────────────────────────

    def _parse(self, regex: str) -> dict:
        """Entry point parsing regex → NFA."""
        self._pos = 0
        self._regex = regex
        result = self._parse_expr()
        if self._pos != len(self._regex):
            raise ValueError(f"Unexpected character at position {self._pos}: '{self._regex[self._pos]}'")
        return result

    def _parse_expr(self) -> dict:
        """Parse expression dengan operator | (union)."""
        left = self._parse_concat()
        while self._pos < len(self._regex) and self._regex[self._pos] == "|":
            self._pos += 1  # consume '|'
            right = self._parse_concat()
            left = self._union(left, right)
        return left

    def _parse_concat(self) -> dict:
        """Parse concatenation (implicit)."""
        result = None
        while self._pos < len(self._regex) and self._regex[self._pos] not in ("|", ")"):
            piece = self._parse_quantifier()
            if result is None:
                result = piece
            else:
                result = self._concat(result, piece)
        if result is None:
            result = self._epsilon_nfa()
        return result

    def _parse_quantifier(self) -> dict:
        """Parse atom + optional quantifier (*, +, ?)."""
        atom = self._parse_atom()
        if self._pos < len(self._regex):
            ch = self._regex[self._pos]
            if ch == "*":
                self._pos += 1
                atom = self._kleene_star(atom)
            elif ch == "+":
                self._pos += 1
                atom = self._plus(atom)
            elif ch == "?":
                self._pos += 1
                atom = self._optional(atom)
        return atom

    def _parse_atom(self) -> dict:
        """Parse atom: karakter, grup (), atau karakter set []."""
        if self._pos >= len(self._regex):
            return self._epsilon_nfa()

        ch = self._regex[self._pos]

        if ch == "(":
            self._pos += 1  # consume '('
            sub = self._parse_expr()
            if self._pos >= len(self._regex) or self._regex[self._pos] != ")":
                raise ValueError("Unmatched '(' dalam regex")
            self._pos += 1  # consume ')'
            return sub

        elif ch == "[":
            # Karakter set: [abc] atau [a-z]
            self._pos += 1  # consume '['
            chars = set()
            while self._pos < len(self._regex) and self._regex[self._pos] != "]":
                if (self._pos + 2 < len(self._regex) and self._regex[self._pos + 1] == "-"
                        and self._regex[self._pos + 2] != "]"):
                    start_ch = self._regex[self._pos]
                    end_ch = self._regex[self._pos + 2]
                    chars.update(chr(c) for c in range(ord(start_ch), ord(end_ch) + 1))
                    self._pos += 3
                else:
                    chars.add(self._regex[self._pos])
                    self._pos += 1
            if self._pos >= len(self._regex):
                raise ValueError("Unmatched '[' dalam regex")
            self._pos += 1  # consume ']'
            # Buat union NFA dari semua karakter di set
            if not chars:
                return self._epsilon_nfa()
            result = self._symbol_nfa(sorted(chars)[0])
            for c in sorted(chars)[1:]:
                result = self._union(result, self._symbol_nfa(c))
            return result

        elif ch == "\\":
            # Escape character
            self._pos += 1
            if self._pos >= len(self._regex):
                raise ValueError("Trailing backslash dalam regex")
            escaped = self._regex[self._pos]
            self._pos += 1
            return self._symbol_nfa(escaped)

        elif ch == ".":
            # Wildcard: kita representasikan sebagai simbol khusus "."
            # (dalam konteks NFA ini, kita matching literal ".")
            # Untuk fullness, treat sebagai symbol "."
            self._pos += 1
            return self._symbol_nfa(".")

        else:
            # Karakter literal
            self._pos += 1
            return self._symbol_nfa(ch)

    def build(self, regex: str) -> dict:
        """
        Bangun NFA dari regex string.
        Return dict dengan keys: states, start, accept, transitions
        """
        if not regex:
            return self._epsilon_nfa()
        return self._parse(regex)

# HELPER: Konversi internal NFA dict → automata-lib NFA object

def internal_to_automata_nfa(nfa_dict: dict) -> NFA:
    """
    Konversi NFA internal (dict format) ke objek automata-lib NFA.
    automata-lib NFA menggunakan frozenset untuk set of states,
    dan "" sebagai epsilon transition.
    """
    states = frozenset(nfa_dict["states"])
    initial_state = nfa_dict["start"]
    final_states = frozenset({nfa_dict["accept"]})

    # Kumpulkan semua simbol (bukan epsilon)
    input_symbols = set()
    for trans in nfa_dict["transitions"].values():
        for sym in trans:
            if sym != "":
                input_symbols.add(sym)
    input_symbols = frozenset(input_symbols)

    # Bangun transitions dalam format automata-lib:
    # {state: {symbol: frozenset(states), ...}, ...}
    transitions = {}
    for state in states:
        transitions[state] = {}
        # Pastikan setiap state punya entry untuk setiap symbol (termasuk "")
        if state in nfa_dict["transitions"]:
            for sym, targets in nfa_dict["transitions"][state].items():
                transitions[state][sym] = frozenset(targets)

    return NFA(
        states=states,
        input_symbols=input_symbols,
        transitions=transitions,
        initial_state=initial_state,
        final_states=final_states,
    )


# HELPER: Visualisasi NFA menggunakan Graphviz

def visualize_nfa(nfa_dict: dict, highlight_path: list = None) -> graphviz.Digraph:
    dot = graphviz.Digraph(
        name="NFA",
        graph_attr={
            "rankdir": "LR",        # Left to Right layout
            "bgcolor": "#1e1e2e",   # Dark background
            "fontname": "Courier New",
            "splines": "curved",
        },
        node_attr={
            "fontname": "Courier New",
            "fontsize": "12",
            "fontcolor": "#cdd6f4",
        },
        edge_attr={
            "fontname": "Courier New",
            "fontsize": "11",
            "fontcolor": "#a6adc8",
            "color": "#585b70",
        },
    )

    highlight_set = set(highlight_path) if highlight_path else set()

    # Node invisible sebagai pointer ke initial state
    dot.node("__start__", shape="none", label="", width="0", height="0")
    dot.edge("__start__", nfa_dict["start"], color="#89b4fa", penwidth="2")

    for state in sorted(nfa_dict["states"]):
        is_accept = (state == nfa_dict["accept"])
        is_start = (state == nfa_dict["start"])
        is_highlighted = state in highlight_set

        # Tentukan style node
        if is_highlighted:
            color = "#a6e3a1"   # Hijau = highlighted path
            fontcolor = "#1e1e2e"
            fillcolor = "#a6e3a1"
            style = "filled,bold"
        elif is_accept:
            color = "#cba6f7"   # Ungu = final state
            fontcolor = "#cba6f7"
            fillcolor = "#313244"
            style = "filled"
        elif is_start:
            color = "#89b4fa"   # Biru = start state
            fontcolor = "#89b4fa"
            fillcolor = "#313244"
            style = "filled"
        else:
            color = "#585b70"
            fontcolor = "#cdd6f4"
            fillcolor = "#313244"
            style = "filled"

        shape = "doublecircle" if is_accept else "circle"

        dot.node(
            state,
            label=state,
            shape=shape,
            color=color,
            fontcolor=fontcolor,
            fillcolor=fillcolor,
            style=style,
        )

    # Tambahkan edges
    # Group edges yang sama arah + state untuk dijadikan satu panah dengan label gabungan
    edge_labels: dict = {}
    for state, trans in nfa_dict["transitions"].items():
        for sym, targets in trans.items():
            label = "ε" if sym == "" else sym
            for target in targets:
                key = (state, target)
                if key not in edge_labels:
                    edge_labels[key] = []
                edge_labels[key].append(label)

    for (src, dst), labels in edge_labels.items():
        combined_label = ", ".join(sorted(labels))
        is_eps = all(l == "ε" for l in labels)
        edge_color = "#f38ba8" if is_eps else "#89dceb"  # merah untuk ε, cyan untuk symbol
        dot.edge(src, dst, label=combined_label, color=edge_color)

    return dot

# HELPER: Simulasi NFA pada string (epsilon-closure based)

def epsilon_closure(states: set, transitions: dict) -> set:
    """Hitung ε-closure dari sekumpulan state."""
    closure = set(states)
    stack = list(states)
    while stack:
        state = stack.pop()
        if state in transitions and "" in transitions[state]:
            for next_state in transitions[state][""]:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
    return closure


def simulate_nfa(nfa_dict: dict, input_string: str) -> tuple[bool, list]:
    """
    Simulasikan NFA pada input_string.
    
    Returns:
        (accepted: bool, path_states: list of set of states per step)
    """
    transitions = nfa_dict["transitions"]
    initial_states = epsilon_closure({nfa_dict["start"]}, transitions)
    
    current_states = initial_states
    path = [set(current_states)]  # path[i] = set of states setelah membaca karakter ke-i

    for char in input_string:
        next_states = set()
        for state in current_states:
            if state in transitions:
                # Cek transisi dengan karakter ini
                if char in transitions[state]:
                    next_states |= transitions[state][char]
                # Cek transisi dengan "." (wildcard)
                if "." in transitions[state]:
                    next_states |= transitions[state]["."]
        # Hitung ε-closure dari next_states
        current_states = epsilon_closure(next_states, transitions)
        path.append(set(current_states))

    accepted = nfa_dict["accept"] in current_states
    return accepted, path

# HELPER: Buat Tabel Transisi NFA

def build_transition_table(nfa_dict: dict) -> tuple[list, list]:
    # Kumpulkan semua simbol (termasuk ε)
    symbols = set()
    for trans in nfa_dict["transitions"].values():
        for sym in trans:
            symbols.add(sym if sym != "" else "ε")
    symbols_sorted = sorted(symbols - {"ε"}) + (["ε"] if "ε" in symbols else [])

    columns = ["State", "Tipe"] + symbols_sorted

    rows = []
    for state in sorted(nfa_dict["states"]):
        row = {"State": state}

        # Tipe state
        tipe = []
        if state == nfa_dict["start"]:
            tipe.append("→ (start)")
        if state == nfa_dict["accept"]:
            tipe.append("* (accept)")
        row["Tipe"] = ", ".join(tipe) if tipe else "-"

        # Transisi
        state_trans = nfa_dict["transitions"].get(state, {})
        for sym_label in symbols_sorted:
            actual_sym = "" if sym_label == "ε" else sym_label
            targets = state_trans.get(actual_sym, set())
            row[sym_label] = "{" + ", ".join(sorted(targets)) + "}" if targets else "∅"

        rows.append(row)

    return columns, rows


# MAIN FEATURE FUNCTION
def show():
    st.header("Feature 2: Regular Expression → NFA & Tes String")
    st.markdown("""
    Masukkan sebuah **regular expression**, dan program akan:
    1. Mem-parse regex menggunakan **Thompson's Construction**
    2. Menampilkan **diagram NFA** yang dihasilkan
    3. Menampilkan **tabel transisi** NFA
    4. Memungkinkan kamu **menguji string** apakah diterima NFA/regex tersebut
    """)

    st.write("---")

    # ─── SECTION 1: Input Regex ───────────────────────────────────────────────
    st.subheader("Langkah 1: Masukkan Regular Expression")

    col_input, col_info = st.columns([2, 1])

    with col_input:
        regex_input = st.text_input(
            "Regular Expression:",
            value="(a|b)*abb",
            placeholder="Contoh: (a|b)*abb",
            help="Operator yang didukung: | (union), * (kleene star), + (plus), ? (optional), () (grouping), [] (karakter set)",
        )

    with col_info:
        with st.expander("Panduan Sintaks Regex", expanded=False):
            st.markdown("""
            | Operator | Arti |
            |----------|------|
            | `a`, `b`, `0-9` | Karakter literal |
            | `\|` | Union (atau) |
            | `*` | Kleene star (0 atau lebih) |
            | `+` | Plus (1 atau lebih) |
            | `?` | Optional (0 atau 1) |
            | `()` | Pengelompokan |
            | `[abc]` | Karakter set |
            | `[a-z]` | Range karakter |
            | `.` | Wildcard (karakter apapun) |
            
            **Contoh:**
            - `(a|b)*abb` → string berisi `abb` di akhir
            - `[0-9]+` → satu atau lebih digit
            - `a?b*` → optional a, lalu nol/lebih b
            """)

    # Tombol Build NFA
    build_btn = st.button("Build NFA dari Regex", type="primary", use_container_width=True)

    # Inisialisasi session state
    if "nfa_dict" not in st.session_state:
        st.session_state.nfa_dict = None
    if "last_regex" not in st.session_state:
        st.session_state.last_regex = ""

    if build_btn and regex_input.strip():
        try:
            with st.spinner("Membangun NFA menggunakan Thompson's Construction..."):
                builder = ThompsonNFA()
                nfa_dict = builder.build(regex_input.strip())
                st.session_state.nfa_dict = nfa_dict
                st.session_state.last_regex = regex_input.strip()
            st.success(f"NFA berhasil dibangun dari regex: `{regex_input}`")
        except ValueError as e:
            st.error(f"Error parsing regex: {e}")
            st.session_state.nfa_dict = None
        except Exception as e:
            st.error(f"Error tidak terduga: {e}")
            st.session_state.nfa_dict = None

    elif build_btn and not regex_input.strip():
        st.warning("Harap masukkan regular expression terlebih dahulu.")

    # SECTION 2: Visualisasi NFA 
    if st.session_state.nfa_dict is not None:
        nfa_dict = st.session_state.nfa_dict

        st.write("---")
        st.subheader("Langkah 2: Diagram & Informasi NFA")

        # Info statistik NFA
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("Jumlah State", len(nfa_dict["states"]))
        with col_s2:
            # Hitung jumlah simbol input
            symbols = {sym for trans in nfa_dict["transitions"].values() for sym in trans if sym != ""}
            st.metric("Simbol Input", len(symbols))
        with col_s3:
            total_trans = sum(
                len(targets)
                for trans in nfa_dict["transitions"].values()
                for targets in trans.values()
            )
            st.metric("Total Transisi", total_trans)
        with col_s4:
            eps_count = sum(
                1 for trans in nfa_dict["transitions"].values() if "" in trans
                for _ in trans[""]
            )
            st.metric("ε-Transisi", eps_count)

        # Tab untuk Diagram dan Tabel
        tab_diagram, tab_table, tab_detail = st.tabs(["Diagram NFA", "Tabel Transisi", "Detail State"])

        with tab_diagram:
            st.markdown("**Visualisasi NFA** (baca dari kiri ke kanan):")
            st.markdown("""
            <div style="display:flex; gap:20px; margin-bottom:10px; font-size:13px;">
                <span><b>Biru</b> = Start state</span>
                <span><b>Ungu</b> = Final state </span>
                <span><b>Hijau</b> = Path saat testing string</span>
                <span><b>Merah</b> = ε-transisi</span>
                <span><b>Cyan</b> = Symbol transisi</span>
            </div>
            """, unsafe_allow_html=True)

            dot = visualize_nfa(nfa_dict)
            st.graphviz_chart(dot.source, use_container_width=True)

        with tab_table:
            st.markdown("**Tabel Transisi NFA:**")
            st.caption("∅ = tidak ada transisi, ε = epsilon transition")

            columns, rows = build_transition_table(nfa_dict)

            # Render tabel manual dengan HTML untuk styling lebih baik
            table_html = "<table style='width:100%; border-collapse:collapse; font-family:monospace;'>"
            # Header
            table_html += "<thead><tr>"
            for col in columns:
                table_html += f"<th style='border:1px solid #585b70; padding:8px; background:#313244; color:#cba6f7; text-align:center;'>{col if col != '' else 'ε'}</th>"
            table_html += "</tr></thead><tbody>"

            for row in rows:
                # Cek apakah accept/start state untuk highlight
                is_accept_row = "*" in row.get("Tipe", "")
                is_start_row = "→" in row.get("Tipe", "")
                row_bg = "#1e2030" if not (is_accept_row or is_start_row) else "#2a2a3e"

                table_html += f"<tr style='background:{row_bg};'>"
                for col in columns:
                    cell = row.get(col, "∅")
                    color = "#cdd6f4"
                    if col == "State":
                        if is_accept_row:
                            color = "#cba6f7"
                        elif is_start_row:
                            color = "#89b4fa"
                    elif cell == "∅":
                        color = "#585b70"
                    table_html += f"<td style='border:1px solid #45475a; padding:8px; color:{color}; text-align:center;'>{cell}</td>"
                table_html += "</tr>"

            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

        with tab_detail:
            st.markdown("**Detail setiap state:**")
            for state in sorted(nfa_dict["states"]):
                is_start = state == nfa_dict["start"]
                is_accept = state == nfa_dict["accept"]

                badge = ""
                if is_start:
                    badge += "`START`"
                if is_accept:
                    badge += "`ACCEPT`"

                with st.expander(f"State **{state}**{badge}"):
                    trans = nfa_dict["transitions"].get(state, {})
                    if not trans:
                        st.write("Tidak ada transisi keluar dari state ini.")
                    else:
                        for sym, targets in sorted(trans.items()):
                            label = "ε (epsilon)" if sym == "" else f"'{sym}'"
                            targets_str = ", ".join(sorted(targets))
                            st.write(f"  → Jika baca **{label}** → `{{{targets_str}}}`")

        # ─── SECTION 3: Tes String ─────────────────────────────────────────────
        st.write("---")
        st.subheader("Langkah 3: Tes String pada NFA")
        st.markdown(f"Regex yang digunakan: `{st.session_state.last_regex}`")

        col_test1, col_test2 = st.columns([3, 1])
        with col_test1:
            test_string = st.text_input(
                "Masukkan string yang ingin diuji:",
                placeholder="Contoh: abb, aabb, bab",
                key="nfa_test_string",
            )
        with col_test2:
            st.write("")  # spacer
            st.write("")  # spacer
            test_btn = st.button("Tes String", type="primary", use_container_width=True)

        if test_btn:
            if test_string is None:
                test_string = ""

            # Simulasi NFA
            accepted_nfa, path = simulate_nfa(nfa_dict, test_string)

            # Cek juga via Python regex sebagai verifikasi
            try:
                pattern = re.compile(f"^{st.session_state.last_regex}$")
                accepted_regex = bool(pattern.match(test_string))
                regex_check_ok = True
            except re.error:
                regex_check_ok = False
                accepted_regex = None

            # Tampilkan hasil
            col_r1, col_r2 = st.columns(2)

            with col_r1:
                if accepted_nfa:
                    st.success(f"String `\"{test_string}\"` **DITERIMA** oleh NFA")
                else:
                    st.error(f"String `\"{test_string}\"` **DITOLAK** oleh NFA")

            with col_r2:
                if regex_check_ok:
                    if accepted_regex:
                        st.success(f"String `\"{test_string}\"` **DITERIMA** oleh Regex Python")
                    else:
                        st.error(f"String `\"{test_string}\"` **DITOLAK** oleh Regex Python")
                else:
                    st.info("Verifikasi via Python regex tidak tersedia untuk regex ini")

            # Tampilkan simulasi step-by-step
            st.markdown("**Simulasi Step-by-Step:**")

            display_string = test_string if test_string else "(string kosong)"
            steps_data = []
            steps_data.append({
                "Langkah": "Awal",
                "Karakter Dibaca": "-",
                "Active States": "{" + ", ".join(sorted(path[0])) + "}",
                "Status": "Processing",
            })

            for i, char in enumerate(test_string):
                states_after = path[i + 1]
                status = "Dead" if not states_after else "Processing"
                steps_data.append({
                    "Langkah": f"Step {i+1}",
                    "Karakter Dibaca": f"'{char}'",
                    "Active States": "{" + ", ".join(sorted(states_after)) + "}" if states_after else "∅ (dead)",
                    "Status": status,
                })

            # Update status langkah terakhir
            final_states = path[-1]
            if nfa_dict["accept"] in final_states:
                steps_data[-1]["Status"] = "Accept"
            else:
                steps_data[-1]["Status"] = "Reject"

            st.dataframe(
                steps_data,
                use_container_width=True,
                hide_index=True,
            )

            # Visualisasi NFA dengan path yang di-highlight
            all_visited = set()
            for state_set in path:
                all_visited |= state_set

            if all_visited:
                st.markdown("**Diagram NFA dengan State yang Dilewati (Hijau):**")
                dot_highlighted = visualize_nfa(nfa_dict, highlight_path=list(all_visited))
                st.graphviz_chart(dot_highlighted.source, use_container_width=True)
    else:
        # Placeholder sebelum NFA dibangun
        st.info("Masukkan regular expression dan klik **Build NFA** untuk memulai.")

        with st.expander("Contoh-Contoh Regex yang Bisa Dicoba"):
            st.markdown("""
            | Regex | Deskripsi | Contoh String Diterima |
            |-------|-----------|------------------------|
            | `(a\|b)*abb` | String diakhiri `abb` | `abb`, `aabb`, `babb` |
            | `[0-9]+` | Satu atau lebih digit | `1`, `42`, `999` |
            | `a*b+` | Nol/lebih `a`, lalu satu/lebih `b` | `b`, `ab`, `aaabb` |
            | `(ab)+` | Satu atau lebih `ab` | `ab`, `abab`, `ababab` |
            | `[a-z][a-z0-9]*` | Identifier: huruf kecil, lalu alphanumeric | `x`, `var1`, `hello` |
            | `0\|(1(01*0)*1)*` | Bilangan biner kelipatan 3 | `0`, `11`, `110` |
            """)