import streamlit as st
from groq import Groq
# to read key val pair from .env
from dotenv import load_dotenv
import os

load_dotenv()
#use os.getenv() with key to get val
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#st stand for streamlit, this giving the app a title, FIX
st.title("English Grammar Tutor")

#start a conversation history 
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

#prompt give to ai agent, FIX 
def get_system_prompt():
    return (
         "You are an English grammar tutor. "
                 "When given a sentence, identify the grammar issue, "
                 "explain the error using simple terms, "
                 "suggest a way to fix the error. "
                 "If the sentence is already correct, say so in an encourage tone, "
                 "briefly explain why it is correct. " 
            )

#get questions from students
def ask_tutor(sentence):
    st.session_state.conversation_history.append({"role": "user", "content": sentence})
		
		#get response from the agent 
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": get_system_prompt()},
            *st.session_state.conversation_history
        ]
    )
    
    
    reply = response.choices[0].message.content
    #append response to history and return response
    st.session_state.conversation_history.append({"role": "assistant", "content": reply})
    return reply

# Display chat history
for message in st.session_state.conversation_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Input
if sentence := st.chat_input("Type a sentence..."):
    with st.chat_message("user"):
        st.write(sentence)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = ask_tutor(sentence)
        st.write(reply)