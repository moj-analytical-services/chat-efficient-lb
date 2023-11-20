"""Streamlit app using LangChain + locally-running Vicuna.

Examples:
    $ streamlit run chatefficient/app_llama2.py
"""
import streamlit as st
from joblib import Memory
from langchain import LLMChain, PromptTemplate
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.llms import LlamaCpp
from langchain.memory import ConversationBufferWindowMemory
from streamlit_chat import message

LOCATION = "./cachedir"
MEMORY = Memory(LOCATION, verbose=0)

# Callbacks support token-wise streaming
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
# Verbose is required to pass to the callback manager
n_gpu_layers = 40  # Change this value based on your model and your GPU VRAM pool.
n_batch = 512  # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.
n_ctx = 512 * 2

# Make sure the model path is correct for your system!
llm = LlamaCpp(
    n_ctx=n_ctx,
    # model_path="./models/llama-7b.ggmlv3.q4_0.bin",
    # model_path="./models/ggml-vic13b-uncensored-q4_0.bin",
    model_path="./models/llama-2-13b-chat.ggmlv3.q4_0.bin",
    n_gpu_layers=n_gpu_layers,
    n_batch=n_batch,
    callback_manager=callback_manager,
    verbose=True,
    pipeline_kwargs={"max_new_tokens": 64 * 4},
    stop=["Human:", "Input:"],
)


# @MEMORY.cache
def generate_response(human_input):
    """Prompt LangChain for a chat completion response."""
    chain = st.session_state["chain"]
    response = chain.predict(human_input=human_input)
    st.session_state["chain"] = chain

    return response


# Initialize session state variables
if "chain" not in st.session_state:
    # template = """
    # You are a helpful assistant.

    # {history}

    # Human: {human_input}
    # Assistant:"""

    template = """
    You are my Mandarin Chinese teacher. I will give you an input in English, and you will
    respond with the corresponding translation in Mandarin Chinese in both pinyin and hanzi.

    Input: {human_input}
    Response:"""

    # prompt = PromptTemplate(input_variables=["history", "human_input"], template=template)
    prompt = PromptTemplate(input_variables=["human_input"], template=template)

    chatgpt_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True,
        memory=ConversationBufferWindowMemory(k=10),
    )
    st.session_state["chain"] = chatgpt_chain


if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []


# Containers
response_container = st.container()
chat_container = st.container()


with chat_container:
    with st.form(key="my_form", clear_on_submit=True):
        user_input = st.text_area("You:", key="input", height=100)
        submit_button = st.form_submit_button(label="Send")

    if submit_button and user_input:
        output = generate_response(user_input).strip()
        st.session_state["past"].append(user_input)
        st.session_state["generated"].append(output)


# INITIAL_MESSAGE = """
# You are a helpful assistant.
# """

INITIAL_MESSAGE = """
You are my Mandarin Chinese teacher. I will give you an input in English, and you will
respond with the corresponding translation in Mandarin Chinese in both pinyin and hanzi.
"""

with response_container:
    message(INITIAL_MESSAGE)
    if st.session_state["generated"]:
        for i in range(len(st.session_state["generated"])):
            message(st.session_state["past"][i], is_user=True, key=f"{i}_user")
            message(st.session_state["generated"][i], key=f"{i}")
