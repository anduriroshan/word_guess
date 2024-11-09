import streamlit as st
import random
import requests
import spacy
import numpy as np

# Load spaCy model with word vectors
@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load('en_core_web_md')
    except OSError:
        st.error("Please install the spaCy model first using: python -m spacy download en_core_web_md")
        return None

nlp = load_spacy_model()

# Function to fetch a random noun
@st.cache_resource
def fetch_random_noun():
    response = requests.get("https://api.datamuse.com/words?rel_jja=noun")
    if response.status_code == 200:
        words = response.json()
        single_word_nouns = [word['word'] for word in words if word['word'].isalpha()]
        if single_word_nouns:
            # Filter words that exist in spaCy's vocabulary
            valid_words = [word for word in single_word_nouns if word in nlp.vocab]
            if valid_words:
                return random.choice(valid_words)
    st.error("Failed to fetch noun or no suitable nouns available")
    return None

# Calculate semantic similarity using spaCy
def calculate_similarity(guess, target):
    if nlp is None:
        return None
    
    # Get spaCy tokens for both words
    guess_token = nlp(guess.lower())[0]
    target_token = nlp(target.lower())[0]
    
    # Check if both words have vectors
    if not guess_token.has_vector or not target_token.has_vector:
        st.warning(f"One or both words don't have semantic vectors. Falling back to string similarity.")
        # Fallback to string similarity
        from difflib import SequenceMatcher
        return SequenceMatcher(None, guess.lower(), target.lower()).ratio()
    
    # Calculate cosine similarity between word vectors
    similarity = guess_token.similarity(target_token)
    return similarity

# Initialize session state for game state management
if 'target_word' not in st.session_state:
    st.session_state.target_word = fetch_random_noun()
if 'attempts' not in st.session_state:
    st.session_state.attempts = 0
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'hints_used' not in st.session_state:
    st.session_state.hints_used = 0

def reset_game():
    st.session_state.target_word = fetch_random_noun()
    st.session_state.attempts = 0
    st.session_state.game_over = False
    st.session_state.hints_used = 0

# Main game UI
st.title("Word Guesser Game")

if st.session_state.target_word:
    st.write(f"Try to guess the noun! (Attempt #{st.session_state.attempts + 1})")
    
    user_guess = st.text_input("Enter your guess:", key="guess_input")
    
    if user_guess and not st.session_state.game_over:
        st.session_state.attempts += 1
        similarity_score = calculate_similarity(user_guess, st.session_state.target_word)
        
        if similarity_score is not None:
            st.write(f"Similarity Score: {similarity_score:.2f}")
            
            if similarity_score > 0.85:  # Adjusted threshold for semantic similarity
                st.success(f"🎉 Correct! The word was '{st.session_state.target_word}'")
                st.session_state.game_over = True
            elif similarity_score > 0.7:
                st.warning("Very close! Try a similar word!")
            elif similarity_score > 0.5:
                st.info("You're getting warmer!")
            else:
                st.write("Not quite, keep trying!")
            
            # Show some related words as context
            if similarity_score > 0.3:
                guess_token = nlp(user_guess.lower())[0]
                related_words = []
                for word in guess_token.vocab:
                    if word.has_vector and word.is_alpha and len(word.text) > 2:
                        similarity = word.similarity(nlp(st.session_state.target_word)[0])
                        if 0.3 < similarity < 0.85:
                            related_words.append((word.text, similarity))
                related_words.sort(key=lambda x: x[1], reverse=True)
                if related_words[:3]:
                    st.write("Some words in this semantic space:", 
                            ", ".join(f"{word}" for word, _ in related_words[:3]))
        
        if st.session_state.attempts >= 10 and not st.session_state.game_over:
            st.error(f"Game Over! The word was '{st.session_state.target_word}'")
            st.session_state.game_over = True
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Get a Hint") and st.session_state.hints_used < 3:
            st.session_state.hints_used += 1
            if st.session_state.hints_used == 1:
                st.write(f"The word has {len(st.session_state.target_word)} letters")
            elif st.session_state.hints_used == 2:
                st.write(f"The word starts with '{st.session_state.target_word[0]}'")
            else:
                # Give a semantic hint using a similar word
                target_token = nlp(st.session_state.target_word)[0]
                similar_words = []
                for word in target_token.vocab:
                    if word.has_vector and word.is_alpha and len(word.text) > 2:
                        similarity = word.similarity(target_token)
                        if 0.5 < similarity < 0.85:
                            similar_words.append((word.text, similarity))
                if similar_words:
                    hint_word = max(similar_words, key=lambda x: x[1])[0]
                    st.write(f"Think of words similar to: {hint_word}")
    
    with col2:
        if st.button("New Game"):
            reset_game()
            st.experimental_rerun()

    # Show attempt counter and hints remaining
    st.sidebar.write(f"Attempts remaining: {10 - st.session_state.attempts}")
    st.sidebar.write(f"Hints remaining: {3 - st.session_state.hints_used}")

else:
    st.error("No target word available for guessing. Please try refreshing the page.")