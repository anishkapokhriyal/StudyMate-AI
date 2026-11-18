import streamlit as st

st.set_page_config(
    page_title="StudyMate AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 StudyMate AI")
st.subheader("Your Personal AI Learning Assistant")

st.write(
    "Welcome to StudyMate AI! "
    "Learn smarter, practise better and achieve more."
)

name = st.text_input("What is your name?")

if name:
    st.success(f"Welcome, {name}! Let's start learning.")

st.divider()

st.header("What would you like to do today?")

subject = st.selectbox(
    "Choose your subject",
    ["Science", "Mathematics", "English", "History", "Geography"]
)

topic = st.text_input("Enter the topic you want to study")

if st.button("Start Learning"):
    if topic:
        st.info(f"Great! Let's study {topic} in {subject}.")
    else:
        st.warning("Please enter a topic first.")