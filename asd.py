import streamlit as st

st.title("Test Button")
bt=st.button("Delete Expense")
print(bt)
if bt :
    st.success("Button clicked!")
else:
    st.info("Button not clicked.")