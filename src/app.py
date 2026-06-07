import streamlit as st

import feature1
import feature2
import feature3
import feature4

# Konfigurasi Halaman
st.set_page_config(page_title="Automata & Regex Tester", layout="wide")
st.title("Automata & Regular Expression Analyzer")
st.markdown("Program ini dibuat untuk memproses DFA, NFA, dan Regular Expression.")

# --- Sidebar untuk Navigasi ---
st.sidebar.header("Pilih Menu")
menu = st.sidebar.radio(
    "Operasi yang tersedia:",
    ("1. Tes Input String pada DFA", 
     "2. Regex ke NFA & Tes String", 
     "3. Minimalisasi DFA", 
     "4. Ekuivalensi Dua DFA")
)

st.write("---")

if menu == "1. Tes Input String pada DFA":
    feature1.show()
elif menu == "2. Regex ke NFA & Tes String":
    feature2.show()
elif menu == "3. Minimalisasi DFA":
    feature3.show()
elif menu == "4. Ekuivalensi Dua DFA":
    feature4.show()
