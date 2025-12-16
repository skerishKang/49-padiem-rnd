import os
import google.generativeai as genai
import streamlit as st

def get_api_key():
    """Retrieves Gemini API Key from environment or session state."""
    return os.getenv("GEMINI_API_KEY") or st.session_state.get("gemini_api_key")

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translates text using Google Gemini API.
    
    Args:
        text: The text to translate.
        source_lang: The source language name (e.g., "한국어").
        target_lang: The target language name (e.g., "English").
        
    Returns:
        The translated text.
    """
    api_key = get_api_key()
    
    if not api_key:
        return f"[Error: Missing API Key] {text}"
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        You are a professional interpreter. Translate the following text from {source_lang} to {target_lang}.
        Output ONLY the translated text, without any explanations or quotes.
        
        Text: {text}
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        return f"[Translation Error] {str(e)}"

def translate_text_stream(text: str, source_lang: str, target_lang: str):
    """
    Translates text using Google Gemini API with streaming.
    Yields chunks of translated text.
    """
    api_key = get_api_key()
    if not api_key:
        yield f"[Error: Missing API Key] {text}"
        return

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        You are a professional interpreter. Translate the following text from {source_lang} to {target_lang}.
        Output ONLY the translated text, without any explanations or quotes.
        
        Text: {text}
        """
        
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"[Translation Error] {str(e)}"
