import json
import re
import streamlit as st
from automata.fa.nfa import NFA

def show():
    st.header("2. Regex ke NFA & Tes String")
    st.write("Masukkan Regular Expression untuk menghasilkan Non-Deterministic Finite Automaton (NFA) yang ekuivalen, lalu uji string terhadap Regex dan NFA tersebut.")

    with st.expander("Panduan Sintaks Regular Expression"):
        st.markdown("""
        Program ini mendukungan operator Regular Expression standar pada teori bahasa formal:
        
        * **Karakter Literal (misal: `a`, `b`, `0`, `1`)**: Mewakili simbol input secara langsung.
        * **Konkatenasi (`ab`)**: Menggabungkan simbol tanpa spasi. Contoh: `ab` berarti 'a' diikuti oleh 'b'.
        * **Union / Alternasi (`|`)**: Operator ATAU (OR). Contoh: `a|b` berarti menerima 'a' atau menerima 'b'.
        * **Kleene Star (`*`)**: Perulangan $0$ kali atau lebih. Contoh: `a*` bisa menerima string kosong (ε), 'a', 'aa', 'aaa', dst.
        * **Kleene Plus (`+`)**: Perulangan $1$ kali atau lebih. Contoh: `a+` menerima 'a', 'aa', 'aaa' (tidak boleh string kosong).
        * **Opsional (`?`)**: Muncul $0$ atau $1$ kali. Contoh: `a?b` akan menerima 'b' atau 'ab'.
        * **Tanda Kurung `()`**: Digunakan untuk mengelompokkan operasi dan mengatur prioritas. Contoh: `(a|b)*c` berarti kombinasi a/b sebanyak apapun yang diakhiri dengan huruf 'c'.
        """)

    # Membagi layout input menjadi dua kolom agar lebih rapi
    col1, col2 = st.columns(2)
    with col1:
        regex_input = st.text_input("Regular Expression", value="a*b|c", help="Gunakan operator standar seperti *, |, atau konkatenasi langsung.")
    with col2:
        test_string = st.text_input("String untuk Dites", value="aab")

    if st.button("Generate NFA & Tes String", type="primary"):
        if not regex_input:
            st.warning("Ekspresi reguler tidak boleh kosong.")
            return
            
        try:
            # Mengonversi Regex ke NFA
            nfa = NFA.from_regex(regex_input)
            st.success("NFA berhasil di-generate dari Regular Expression!")
            
            # Menampilkan definisi formal NFA di dalam expander
            with st.expander("Lihat Detail Definisi Formal NFA"):
                st.write("**States (Q):**", str(nfa.states))
                st.write("**Input Symbols (Σ):**", str(nfa.input_symbols))
                st.write("**Initial State (q0):**", str(nfa.initial_state))
                st.write("**Final States (F):**", str(nfa.final_states))
                st.write("**Transitions (δ):**")
                # Menampilkan dictionary transisi dalam format JSON agar mudah dibaca
                st.json(nfa.transitions)

            st.divider()

            # Mengetes string pada NFA & Regex
            st.subheader("Hasil Pengujian")
            
            res_col1, res_col2 = st.columns(2)
            
            # Tes menggunakan engine NFA dari automata-lib
            with res_col1:
                st.markdown("**Hasil Tes NFA:**")
                try:
                    if nfa.accepts_input(test_string):
                        st.success(f"String '{test_string}' **DITERIMA** oleh NFA.")
                    else:
                        st.error(f"String '{test_string}' **DITOLAK** oleh NFA.")
                except Exception:
                    # Menangkap error jika string mengandung karakter di luar alphabet NFA
                    st.error(f"String '{test_string}' **DITOLAK** (Mengandung simbol yang tidak dikenali NFA).")
            
            # Tes menggunakan engine Regex bawaan Python (re) sebagai validasi silang
            with res_col2:
                st.markdown("**Hasil Tes Regex Engine:**")
                # re.fullmatch memastikan seluruh string cocok sepenuhnya dari awal hingga akhir
                if re.fullmatch(regex_input, test_string):
                    st.success(f"String '{test_string}' **COCOK** dengan Regex.")
                else:
                    st.error(f"String '{test_string}' **TIDAK COCOK** dengan Regex.")

        except Exception as e:
            st.error(f"Gagal meng-generate NFA. Pastikan sintaks regex valid sesuai standar teori automata. Error detail: `{e}`")