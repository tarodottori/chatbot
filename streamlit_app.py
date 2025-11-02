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
debug_mode = st.checkbox("デバッグモード", value=True)

if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🗝️")
else:
    # Gemini API endpoint
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
        
        # Make API request with streaming
        try:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                if debug_mode:
                    debug_info = st.expander("デバッグ詳細")
                
                # Send POST request to Gemini API with streaming
                response = requests.post(
                    f"{GEMINI_API_URL}?key={gemini_api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    stream=True,
                    timeout=120
                )
                
                if debug_mode:
                    with debug_info:
                        st.write(f"**HTTPステータスコード:** {response.status_code}")
                        st.write(f"**レスポンスヘッダー:** {dict(response.headers)}")
                
                if response.status_code == 200:
                    line_count = 0
                    # Process streaming response
                    for line in response.iter_lines():
                        if line:
                            line_count += 1
                            line_text = line.decode('utf-8')
                            
                            if debug_mode:
                                with debug_info:
                                    st.write(f"**受信ライン {line_count}:**")
                                    st.code(line_text)
                            
                            # Remove "data: " prefix if present
                            if line_text.startswith('data: '):
                                line_text = line_text[6:]
                            
                            try:
                                chunk_data = json.loads(line_text)
                                
                                if debug_mode:
                                    with debug_info:
                                        st.write(f"**パース済みJSON {line_count}:**")
                                        st.json(chunk_data)
                                
                                # Extract text from the response
                                if 'candidates' in chunk_data:
                                    for candidate in chunk_data['candidates']:
                                        if 'content' in candidate:
                                            for part in candidate['content'].get('parts', []):
                                                if 'text' in part:
                                                    text_chunk = part['text']
                                                    full_response += text_chunk
                                                    if debug_mode:
                                                        with debug_info:
                                                            st.write(f"**抽出テキスト:** {text_chunk}")
                                                    message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError as je:
                                if debug_mode:
                                    with debug_info:
                                        st.error(f"JSON decode error: {str(je)}")
                                continue
                    
                    if debug_mode:
                        with debug_info:
                            st.write(f"**総受信ライン数:** {line_count}")
                            st.write(f"**最終レスポンス:** {full_response}")
                    
                    message_placeholder.markdown(full_response)
                    
                    if not full_response:
                        st.warning("警告: レスポンスが空です")
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
