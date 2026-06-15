import json
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
        test_string = st.text_input("String untuk Dites", value="11", help="String yang akan diuji terhadap DFA.")
        st.markdown("**Mode pengujian:**")
        mode = st.radio(
            "Mode pengujian",
            ("Satu string (dengan trace transisi)", "Banyak string sekaligus"),
            label_visibility="collapsed"
        )
        if mode == "Banyak string sekaligus":
            multi_input = st.text_area("Daftar String (satu per baris)", height=150, help="Masukkan beberapa string, satu per baris.")

    if st.button("Buat DFA & Tes String", type="primary"):
        if not json_input.strip():
            st.warning("Definisi DFA tidak boleh kosong.")
            return

        # Parse JSON
        try:
            dfa_data = json.loads(json_input)
        except json.JSONDecodeError as e:
            st.error(f"Format JSON tidak valid: {e}")
            return

        # Buat objek DFA
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

        # Tampilkan tabel transisi
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
            # Validasi simbol
            invalid = sorted(set(test_string) - dfa.input_symbols)
            if invalid:
                st.error(f"String mengandung simbol yang tidak ada di alfabet DFA: `{'`, `'.join(invalid)}`")
                return

            accepted = dfa.accepts_input(test_string)

            if accepted:
                st.success(f"String `'{test_string}'` **DITERIMA** oleh DFA.")
            else:
                st.error(f"String `'{test_string}'` **DITOLAK** oleh DFA.")

            # Trace transisi step-by-step
            st.markdown("**Jejak Transisi (Trace):**")
            path = [dfa.initial_state]
            cur = dfa.initial_state
            for sym in test_string:
                cur = dfa.transitions[cur][sym]
                path.append(cur)

            if test_string:
                for i, sym in enumerate(test_string):
                    is_final = path[i+1] in dfa.final_states
                    marker = " ✅" if (i == len(test_string) - 1 and accepted) else ""
                    st.write(f"**{path[i]}** --( `{sym}` )--> **{path[i+1]}**{marker}")
            else:
                st.write(f"String kosong (ε) — langsung di state awal: **{dfa.initial_state}**")

            final_state = path[-1]
            status = "**FINAL** (menerima)" if final_state in dfa.final_states else "bukan final (menolak)"
            st.markdown(f"**State akhir:** `{final_state}` — {status}")
            st.markdown(f"**Lintasan:** `{'  →  '.join(path)}`")

        else:
            # Mode banyak string
            lines = [l.strip() for l in multi_input.splitlines() if l.strip() != ""]
            if not lines:
                st.warning("Belum ada string yang dimasukkan.")
                return

            results = []
            for s in lines:
                invalid = sorted(set(s) - dfa.input_symbols)
                if invalid:
                    results.append({"String": s, "Hasil": "Error", "Keterangan": f"Simbol tidak valid: {', '.join(invalid)}"})
                    continue
                accepted = dfa.accepts_input(s)
                results.append({
                    "String": s if s else "(ε)",
                    "Hasil": "✅ Diterima" if accepted else "❌ Ditolak",
                    "Keterangan": ""
                })

            st.table(results)

            total = len(results)
            diterima = sum(1 for r in results if r["Hasil"].startswith("✅"))
            ditolak  = sum(1 for r in results if r["Hasil"].startswith("❌"))
            error    = sum(1 for r in results if r["Hasil"] == "Error")
            st.markdown(f"**Total:** {total} &nbsp;|&nbsp; **Diterima:** {diterima} &nbsp;|&nbsp; **Ditolak:** {ditolak} &nbsp;|&nbsp; **Error:** {error}")