from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import streamlit as st
import openai

st.set_page_config(layout="wide")

key_vault_name = "kv-5amfwtmscpp4a"
key_vault_uri = f"https://kv-5amfwtmscpp4a.vault.azure.net/"
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_uri, credential=credential)

def get_secret(secret_name):
    """Fetch a secret from Azure Key Vault."""
    return secret_client.get_secret(secret_name).value

def token_provider():
    """Provide a token for Azure OpenAI."""
    return credential.get_token("https://cognitiveservices.azure.com/.default").token

def create_chat_completion(messages):
    """Create and return a new chat completion request using secrets from Azure Key Vault."""
    aoai_endpoint = get_secret("aoai-endpoint")
    deployment_name = get_secret("aoai-deployment-name")
    search_endpoint = get_secret("search-endpoint")
    search_key = get_secret("search-key")
    search_index_name = get_secret("search-index-name")

    client = openai.AzureOpenAI(
        azure_ad_token_provider=token_provider,  # Pass the callable function
        api_version="2024-06-01",
        azure_endpoint=aoai_endpoint
    )

    # Create and return a new chat completion request
    return client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ],
        stream=True,
        extra_body={
            "data_sources": [
                {
                    "type": "azure_search",
                    "parameters": {
                        "endpoint": search_endpoint,
                        "index_name": search_index_name,
                        "authentication": {
                            "type": "api_key",
                            "key": search_key
                        }
                    }
                }
            ]
        }
    )

def handle_chat_prompt(prompt):
    """Echo the user's prompt to the chat window.
    Then, send the user's prompt to Azure OpenAI and display the response."""

    # Echo the user's prompt to the chat window
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
 
    # Send the user's prompt to Azure OpenAI and display the response
    # The call to Azure OpenAI is handled in create_chat_completion()
    # This function loops through the responses and displays them as they come in.
    # It also appends the full response to the chat history.
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in create_chat_completion(st.session_state.messages):
            if response.choices:
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

def main():
    """Main function for the Chat with Data Streamlit app."""

    st.write(
    """
    # Chat with Data

    This Streamlit dashboard is intended to show off capabilities of Azure OpenAI, including integration with AI Search.
    """
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Await a user message and handle the chat prompt when it comes in.
    if prompt := st.chat_input("Enter a message:"):
        handle_chat_prompt(prompt)

if __name__ == "__main__":
    main()
