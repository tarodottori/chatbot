import streamlit as st
import requests
import json

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini API to generate responses. "
    "To use this app, you need to provide a Gemini API key, which you can get [here](https://makersuite.google.com/app/apikey). "
)

# Ask user for their Gemini API key via `st.text_input`.
gemini_api_key = st.text_input("Gemini API Key", type="password")

# デバッグモードの追加
debug_mode = st.checkbox("デバッグモード", value=False)

if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🗝️")
else:
    # Gemini API endpoint - ストリーミングではなく通常のエンドポイントを使用
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
    
    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("What is up?"):
        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Prepare the request payload for Gemini API
        # Convert chat history to Gemini format
        contents = []
        for m in st.session_state.messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })
        
        payload = {
            "contents": contents
        }
        
        if debug_mode:
            st.write("### デバッグ情報")
            st.write("**リクエストURL:**", f"{GEMINI_API_URL}?key=****")
            st.write("**リクエストペイロード:**")
            st.json(payload)
        
        # Make API request
        try:
            with st.chat_message("assistant"):
                if debug_mode:
                    debug_info = st.expander("デバッグ詳細")
                
                # Send POST request to Gemini API
                response = requests.post(
                    f"{GEMINI_API_URL}?key={gemini_api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=120
                )
                
                if debug_mode:
                    with debug_info:
                        st.write(f"**HTTPステータスコード:** {response.status_code}")
                        st.write(f"**レスポンスヘッダー:** {dict(response.headers)}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if debug_mode:
                        with debug_info:
                            st.write("**完全なレスポンスJSON:**")
                            st.json(response_data)
                    
                    # Extract text from the response
                    full_response = ""
                    if 'candidates' in response_data:
                        for candidate in response_data['candidates']:
                            if 'content' in candidate:
                                for part in candidate['content'].get('parts', []):
                                    if 'text' in part:
                                        full_response += part['text']
                    
                    if debug_mode:
                        with debug_info:
                            st.write(f"**抽出されたテキスト:** {full_response}")
                    
                    if full_response:
                        st.markdown(full_response)
                    else:
                        st.warning("警告: レスポンスが空です")
                        full_response = "（応答なし）"
                else:
                    error_message = f"API Error: {response.status_code}"
                    try:
                        error_data = response.json()
                        if debug_mode:
                            with debug_info:
                                st.write("**エラーレスポンス:**")
                                st.json(error_data)
                        if 'error' in error_data:
                            error_message = error_data['error'].get('message', error_message)
                    except:
                        if debug_mode:
                            with debug_info:
                                st.write("**生のエラーレスポンス:**")
                                st.code(response.text)
                    
                    st.error(error_message)
                    full_response = f"Error: {error_message}"
            
            # Store the assistant's response
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except requests.exceptions.RequestException as e:
            st.error(f"API通信エラー: {str(e)}")
            if debug_mode:
                st.exception(e)
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
