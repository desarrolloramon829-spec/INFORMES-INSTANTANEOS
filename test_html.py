import streamlit as st

st.markdown("## Pruebas de HTML")

# 1. No indentation, without newline
st.markdown("### Test 1")
st.markdown('<section class="editorial-hero scene-seq seq-1"><h1>Análisis 1</h1></section>', unsafe_allow_html=True)

# 2. No indentation, with newline
st.markdown("### Test 2")
st.markdown('<section class="editorial-hero scene-seq seq-1">\n<h1>Análisis 2</h1>\n</section>', unsafe_allow_html=True)

# 3. With f-string spaces and empty line (like first failure)
st.markdown("### Test 3")
st.markdown(f"""
    <section class="editorial-hero scene-seq seq-1">
        
        <h1>Análisis 3</h1>
    </section>
""", unsafe_allow_html=True)

# 4. f-string without empty lines
st.markdown("### Test 4")
st.markdown(f"""
    <section class="editorial-hero scene-seq seq-1">
        <h1>Análisis 4</h1>
    </section>
""", unsafe_allow_html=True)

# 5. Using textwrap dedent
import textwrap
st.markdown("### Test 5")
st.markdown(textwrap.dedent(f"""
    <section class="editorial-hero scene-seq seq-1">
        <h1>Análisis 5</h1>
    </section>
"""), unsafe_allow_html=True)

