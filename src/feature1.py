import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from automata.fa.dfa import DFA
import streamlit as st


CONTOH_DFA = {
    "states": ["q0", "q1", "q2"],
    "input_symbols": ["0", "1"],
    "transitions": {
        "q0": {"0": "q0", "1": "q1"},
        "q1": {"0": "q2", "1": "q0"},
        "q2": {"0": "q1", "1": "q2"}
    },
    "initial_state": "q0",
    "final_states": ["q0"]
}


def draw_dfa(dfa, trace_path=None):
    G = nx.MultiDiGraph()
    states = sorted(dfa.states)
    for s in states:
        G.add_node(s)

    edge_labels = {}
    for from_s, trans in dfa.transitions.items():
        for sym, to_s in trans.items():
            edge_labels.setdefault((from_s, to_s), []).append(sym)
    for (u, v), syms in edge_labels.items():
        G.add_edge(u, v)

    # Layout melingkar supaya rapi
    n = len(states)
    if n == 1:
        pos = {states[0]: (0.5, 0.5)}
    else:
        pos = {}
        for i, s in enumerate(states):
            angle = 2 * math.pi * i / n
            pos[s] = (math.cos(angle), math.sin(angle))

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    visited = set(trace_path) if trace_path else set()
    trace_edges = set()
    if trace_path:
        for i in range(len(trace_path) - 1):
            trace_edges.add((trace_path[i], trace_path[i + 1]))

    node_list = list(G.nodes())
    node_colors, node_edgecolors = [], []
    for s in node_list:
        if trace_path and s in visited:
            node_colors.append("#FACC15"); node_edgecolors.append("#92400E")
        elif s == dfa.initial_state and s in dfa.final_states:
            node_colors.append("#34D399"); node_edgecolors.append("#065F46")
        elif s == dfa.initial_state:
            node_colors.append("#2DD4BF"); node_edgecolors.append("#0F6E56")
        elif s in dfa.final_states:
            node_colors.append("#A5B4FC"); node_edgecolors.append("#4338CA")
        else:
            node_colors.append("#6B7280"); node_edgecolors.append("#374151")

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=2000, linewidths=2.5,
                           edgecolors=node_edgecolors)

    # Double circle untuk final state
    for s in dfa.final_states:
        if s in pos:
            x, y = pos[s]
            ec = "#92400E" if (trace_path and s in visited) else "#4338CA"
            circle = plt.Circle((x, y), 0.155, fill=False,
                                 edgecolor=ec, linewidth=2,
                                 transform=ax.transData)
            ax.add_patch(circle)

    font_colors = []
    for s in node_list:
        if trace_path and s in visited:
            font_colors.append("#1C1917")
        else:
            font_colors.append("white")

    for s, fc in zip(node_list, font_colors):
        x, y = pos[s]
        ax.text(x, y, s, ha="center", va="center",
                fontsize=11, fontweight="bold", color=fc)

    # Gambar edge
    for (u, v), syms in edge_labels.items():
        label = ", ".join(sorted(syms))
        color = "#F59E0B" if (u, v) in trace_edges else "#9CA3AF"
        width = 2.5 if (u, v) in trace_edges else 1.2

        if u == v:
            # Self-loop
            x, y = pos[u]
            loop = mpatches.FancyArrowPatch(
                (x - 0.08, y + 0.13), (x + 0.08, y + 0.13),
                connectionstyle="arc3,rad=-2.5",
                arrowstyle="-|>",
                color=color, linewidth=width,
                mutation_scale=15
            )
            ax.add_patch(loop)
            ax.text(x, y + 0.32, label, fontsize=9, color=color,
                    ha="center", va="center")
        else:
            # Cek apakah ada edge balik (bidirectional → kasih rad biar tidak tumpuk)
            has_reverse = (v, u) in edge_labels
            rad = 0.25 if has_reverse else 0.1
            arrow = mpatches.FancyArrowPatch(
                pos[u], pos[v],
                connectionstyle=f"arc3,rad={rad}",
                arrowstyle="-|>",
                color=color, linewidth=width,
                mutation_scale=15,
                shrinkA=22, shrinkB=22
            )
            ax.add_patch(arrow)
            mx = (pos[u][0] + pos[v][0]) / 2
            my = (pos[u][1] + pos[v][1]) / 2
            dx = pos[v][0] - pos[u][0]
            dy = pos[v][1] - pos[u][1]
            norm = max(np.sqrt(dx**2 + dy**2), 0.001)
            offset = rad * 0.6
            ax.text(mx - dy / norm * offset, my + dx / norm * offset,
                    label, fontsize=9, color=color, ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.1", fc="#0e1117", ec="none", alpha=0.7))

    # Panah initial state
    ix, iy = pos[dfa.initial_state]
    ax.annotate("", xy=(ix - 0.18, iy),
                xytext=(ix - 0.35, iy),
                arrowprops=dict(arrowstyle="->", color="#2DD4BF", lw=2))
    ax.text(ix - 0.37, iy + 0.05, "start", fontsize=8,
            color="#2DD4BF", ha="right")

    # Legend
    legend_items = [
        mpatches.Patch(color="#2DD4BF", label="Initial state"),
        mpatches.Patch(color="#A5B4FC", label="Final state"),
        mpatches.Patch(color="#6B7280", label="State biasa"),
    ]
    if trace_path:
        legend_items.append(mpatches.Patch(color="#FACC15", label="State dilewati (trace)"))
        legend_items.append(mpatches.Patch(color="#F59E0B", label="Edge dilewati (trace)"))
    ax.legend(handles=legend_items, loc="upper right",
              facecolor="#1f2937", edgecolor="#374151",
              labelcolor="white", fontsize=9)

    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.5, 1.6)
    ax.axis("off")
    plt.tight_layout()
    return fig


def show():
    st.header("1. Tes Input String pada DFA")
    st.write("Masukkan definisi DFA dalam format JSON, lalu uji apakah suatu string diterima atau ditolak beserta jejak transisinya.")

    with st.expander("Panduan Format JSON & Contoh DFA"):
        st.markdown("""
        DFA didefinisikan sebagai objek JSON dengan field berikut:

        * **`states`** *(list)*: Daftar semua state. Contoh: `["q0", "q1", "q2"]`
        * **`input_symbols`** *(list)*: Daftar simbol alfabet. Contoh: `["0", "1"]`
        * **`transitions`** *(object)*: Fungsi transisi — untuk setiap state, petakan setiap simbol ke state tujuan.
        * **`initial_state`** *(string)*: State awal. Contoh: `"q0"`
        * **`final_states`** *(list)*: Daftar state penerima. Contoh: `["q0"]`

        Contoh DFA yang menerima string biner dengan jumlah digit `1` yang habis dibagi 3:
        """)
        st.code(json.dumps(CONTOH_DFA, indent=2), language="json")

    col1, col2 = st.columns(2)
    with col1:
        json_input = st.text_area(
            "Definisi DFA (JSON)",
            value=json.dumps(CONTOH_DFA, indent=2),
            height=300,
            help="Masukkan definisi DFA dalam format JSON sesuai panduan di atas."
        )
    with col2:
        st.markdown("**Mode pengujian:**")
        mode = st.radio(
            "Mode pengujian",
            ("Satu string (dengan trace transisi)", "Banyak string sekaligus"),
            label_visibility="collapsed",
            key="mode_radio"
        )

        if mode == "Satu string (dengan trace transisi)":
            # Hapus state multi_input supaya tidak tersisa
            if "multi_input" in st.session_state:
                del st.session_state["multi_input"]
            multi_input = ""
            test_string = st.text_input(
                "String untuk Dites",
                value="11",
                help="String yang akan diuji terhadap DFA.",
                key="test_string"
            )
        else:
            # Hapus state test_string supaya tidak tersisa
            if "test_string" in st.session_state:
                del st.session_state["test_string"]
            test_string = ""
            multi_input = st.text_area(
                "Daftar String (satu per baris)",
                height=150,
                help="Masukkan beberapa string, satu per baris.",
                key="multi_input"
            )

    if st.button("Buat DFA & Tes String", type="primary"):
        if not json_input.strip():
            st.warning("Definisi DFA tidak boleh kosong.")
            return

        try:
            dfa_data = json.loads(json_input)
        except json.JSONDecodeError as e:
            st.error(f"Format JSON tidak valid: {e}")
            return

        try:
            dfa = DFA(
                states=set(dfa_data["states"]),
                input_symbols=set(dfa_data["input_symbols"]),
                transitions={s: dict(t) for s, t in dfa_data["transitions"].items()},
                initial_state=dfa_data["initial_state"],
                final_states=set(dfa_data["final_states"]),
            )
        except KeyError as e:
            st.error(f"Field wajib tidak ditemukan dalam JSON: {e}")
            return
        except Exception as e:
            st.error(f"DFA tidak valid: {e}")
            return

        st.success("DFA berhasil dibuat!")

        with st.expander("Lihat Tabel Transisi DFA"):
            symbols = sorted(dfa.input_symbols)
            rows = []
            for state in sorted(dfa.states):
                row = {"State": ("→ " if state == dfa.initial_state else "   ") + ("* " if state in dfa.final_states else "  ") + state}
                for sym in symbols:
                    row[sym] = dfa.transitions.get(state, {}).get(sym, "-")
                rows.append(row)
            st.table(rows)
            st.caption("→ = initial state, * = final state")

        st.divider()
        st.subheader("Hasil Pengujian")

        if mode == "Satu string (dengan trace transisi)":
            if not test_string:
                st.warning("Masukkan string yang akan diuji.")
                return

            invalid = sorted(set(test_string) - dfa.input_symbols)
            if invalid:
                st.error(f"String mengandung simbol yang tidak ada di alfabet DFA: `{'`, `'.join(invalid)}`")
                return

            accepted = dfa.accepts_input(test_string)

            if accepted:
                st.success(f"String `'{test_string}'` **DITERIMA** oleh DFA.")
            else:
                st.error(f"String `'{test_string}'` **DITOLAK** oleh DFA.")

            path = [dfa.initial_state]
            cur = dfa.initial_state
            for sym in test_string:
                cur = dfa.transitions[cur][sym]
                path.append(cur)

            st.markdown("**Graf DFA** *(kuning = state dilewati, oranye = edge dilewati)*")
            fig = draw_dfa(dfa, trace_path=path)
            st.pyplot(fig)
            plt.close(fig)

            st.markdown("**Jejak Transisi (Trace):**")
            if test_string:
                for i, sym in enumerate(test_string):
                    marker = " ✅" if (i == len(test_string) - 1 and accepted) else ""
                    st.write(f"**{path[i]}** --( `{sym}` )--> **{path[i+1]}**{marker}")
            else:
                st.write(f"String kosong (ε) — langsung di state awal: **{dfa.initial_state}**")

            final_state = path[-1]
            status = "**FINAL** (menerima)" if final_state in dfa.final_states else "bukan final (menolak)"
            st.markdown(f"**State akhir:** `{final_state}` — {status}")
            st.markdown(f"**Lintasan:** `{'  →  '.join(path)}`")

        else:
            lines = [l.strip() for l in multi_input.splitlines() if l.strip() != ""]
            if not lines:
                st.warning("Belum ada string yang dimasukkan.")
                return

            results = []

            for s in lines:
                invalid = sorted(set(s) - dfa.input_symbols)

                if invalid:
                    results.append({
                        "String": s,
                        "Trace": "-",
                        "Hasil": f"Error: {', '.join(invalid)}"
                    })
                    continue

                accepted = dfa.accepts_input(s)

                path = [dfa.initial_state]
                cur = dfa.initial_state

                for sym in s:
                    cur = dfa.transitions[cur][sym]
                    path.append(cur)

                results.append({
                    "String": s if s else "(ε)",
                    "Trace": " → ".join(path),
                    "Hasil": "Diterima" if accepted else "Ditolak"
                })

            st.table(results)

            total = len(results)
            diterima = sum(1 for r in results if r["Hasil"].startswith("✅"))
            ditolak = sum(1 for r in results if r["Hasil"].startswith("❌"))
            error = sum(1 for r in results if r["Hasil"].startswith("Error"))

            st.markdown(
                f"**Total:** {total} &nbsp;|&nbsp; "
                f"**Diterima:** {diterima} &nbsp;|&nbsp; "
                f"**Ditolak:** {ditolak} &nbsp;|&nbsp; "
                f"**Error:** {error}"
            )