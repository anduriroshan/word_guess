import streamlit as st
import random
import requests
import nltk
from nltk.corpus import wordnet
from difflib import SequenceMatcher

# Download required NLTK data
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')

# Function to fetch a random noun
@st.cache_resource
def fetch_random_noun():
    response = requests.get("https://api.datamuse.com/words?rel_jja=noun")
    if response.status_code == 200:
        words = response.json()
        single_word_nouns = [word['word'] for word in words if word['word'].isalpha()]
        if single_word_nouns:
            return random.choice(single_word_nouns)
    st.error("Failed to fetch noun or no suitable nouns available")
    return None

# Calculate semantic similarity and return score from 1000 to 0
def calculate_similarity(guess, target):
    guess_synsets = wordnet.synsets(guess.lower())
    target_synsets = wordnet.synsets(target.lower())
    
    if not guess_synsets or not target_synsets:
        return 1000 - int(SequenceMatcher(None, guess.lower(), target.lower()).ratio() * 1000)
    
    max_similarity = 0
    for guess_syn in guess_synsets:
        for target_syn in target_synsets:
            similarity = guess_syn.path_similarity(target_syn)
            if similarity and similarity > max_similarity:
                max_similarity = similarity
    
    return int((1 - max_similarity) * 1000) if max_similarity > 0 else 1000

def get_semantic_hints(word, num_hints=3):
    """Get different types of semantically related words as hints"""
    hints = set()
    synsets = wordnet.synsets(word)
    
    if synsets:
        primary_synset = synsets[0]
        
        # Get synonyms
        for lemma in primary_synset.lemmas():
            if lemma.name() != word and len(lemma.name()) > 2:
                hints.add(("synonym", lemma.name()))
        
        # Get hypernyms (more general terms)
        for hypernym in primary_synset.hypernyms():
            for lemma in hypernym.lemmas():
                if lemma.name() != word and len(lemma.name()) > 2:
                    hints.add(("category", lemma.name()))
        
        # Get hyponyms (more specific terms)
        for hyponym in primary_synset.hyponyms():
            for lemma in hyponym.lemmas():
                if lemma.name() != word and len(lemma.name()) > 2:
                    hints.add(("similar", lemma.name()))

        # Get holonyms (whole of which the word is a part)
        for holonym in primary_synset.member_holonyms() + primary_synset.part_holonyms():
            for lemma in holonym.lemmas():
                if lemma.name() != word and len(lemma.name()) > 2:
                    hints.add(("related", lemma.name()))

    # Convert hints to list and shuffle
    hints_list = list(hints)
    random.shuffle(hints_list)
    return hints_list[:num_hints]

# Initialize session state
if 'target_word' not in st.session_state:
    st.session_state.target_word = 'condom'
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
        
        st.write(f"Similarity Score: {similarity_score}")
        
        if similarity_score == 0:
            st.success(f"🎉 Correct! The word was '{st.session_state.target_word}'")
            st.session_state.game_over = True
        elif similarity_score <= 20:
            st.warning("Almost there.........")
        elif similarity_score <= 200:
            st.warning("Very close! Try a similar word!")
            related = get_semantic_hints(user_guess, 2)
            if related:
                st.write("Some related words:")
                for hint_type, word in related:
                    st.write(f"- {word} ({hint_type})")
        elif similarity_score <= 500:
            st.info("You're getting warmer!")
        else:
            st.write("Not quite, keep trying!")
        
        if st.session_state.attempts >= 10 and not st.session_state.game_over:
            st.error(f"Game Over! The word was '{st.session_state.target_word}'")
            st.session_state.game_over = True
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Get a Hint") and st.session_state.hints_used < 3:
            st.session_state.hints_used += 1
            new_hints = get_semantic_hints(st.session_state.target_word)
            if new_hints:
                hint_type, hint_word = random.choice(new_hints)
                st.write(f"Hint: Think of words like '{hint_word}' ({hint_type})")
            else:
                st.write("Sorry, couldn't generate a hint right now.")
    
    with col2:
        if st.button("New Game"):
            reset_game()
            st.rerun()

    # Show attempt counter and hints remaining
    st.sidebar.write(f"Attempts remaining: {10 - st.session_state.attempts}")
    st.sidebar.write(f"Hints remaining: {3 - st.session_state.hints_used}")

else:
    st.error("No target word available for guessing. Please try refreshing the page.")
