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

def get_semantic_hints(word):
    """Get all synonyms and hypernyms as hints"""
    hints = []
    synsets = wordnet.synsets(word)
    
    if synsets:
        primary_synset = synsets[0]
        
        # Get synonyms
        for lemma in primary_synset.lemmas():
            if lemma.name() != word and len(lemma.name()) > 2:
                hints.append(("synonym", lemma.name()))
        
        # Get all hypernyms (including inherited)
        hypernym_paths = primary_synset.hypernym_paths()
        for path in hypernym_paths:
            for hypernym in path:
                for lemma in hypernym.lemmas():
                    if lemma.name() != word and len(lemma.name()) > 2:
                        hints.append(("category", lemma.name()))

    # Remove duplicates while preserving order
    seen = set()
    unique_hints = []
    for hint in hints:
        if hint[1] not in seen:
            seen.add(hint[1])
            unique_hints.append(hint)
    
    # Shuffle the hints to mix synonyms and categories
    random.shuffle(unique_hints)
    return unique_hints

# Initialize session state
if 'target_word' not in st.session_state:
    st.session_state.target_word = fetch_random_noun()
if 'game_over' not in st.session_state:
    st.session_state.game_over = False
if 'previous_guesses' not in st.session_state:
    st.session_state.previous_guesses = {}
if 'hints' not in st.session_state:
    st.session_state.hints = []
if 'used_hints' not in st.session_state:
    st.session_state.used_hints = []
if 'hint_count' not in st.session_state:
    st.session_state.hint_count = 0

def reset_game():
    st.session_state.target_word = fetch_random_noun()
    st.session_state.game_over = False
    st.session_state.previous_guesses = {}
    st.session_state.hints = []
    st.session_state.used_hints = []
    st.session_state.hint_count = 0

# Main game UI
st.title("Word Guesser Game")

if st.session_state.target_word:
    st.write("Try to guess the word!")
    
    # Create a form for the guess input and submit button
    with st.form(key='guess_form'):
        user_guess = st.text_input("Enter your guess:", key="guess_input")
        submit_guess = st.form_submit_button("Submit Guess")
    
    # Process guess only when submit button is clicked
    if submit_guess and user_guess:
        if user_guess.lower() in st.session_state.previous_guesses:
            st.warning(f"You've already guessed '{user_guess}'! Try a different word.")
        elif not st.session_state.game_over:
            similarity_score = calculate_similarity(user_guess, st.session_state.target_word)
            st.session_state.previous_guesses[user_guess.lower()] = similarity_score
            
            st.write(f"You are {similarity_score} miles far away from the answer.")
            
            if similarity_score == 0:
                st.success(f"🎉 Correct! The word was '{st.session_state.target_word}'")
                st.session_state.game_over = True
            elif similarity_score <= 20:
                st.warning("Almost there.........")
            elif similarity_score <= 200:
                st.warning("Very close! Try a similar word!")
            elif similarity_score <= 500:
                st.info("You're getting warmer!")
            else:
                st.write("Not quite, keep trying!")

    # Game control buttons
    col1, col2, col3, _, col5 = st.columns(5)
    with col1:
        if st.button("Get Hint"):
            # Generate hints if not already generated
            if not st.session_state.hints:
                st.session_state.hints = get_semantic_hints(st.session_state.target_word)
            
            # If we have hints available
            if st.session_state.hints:
                if st.session_state.hint_count < len(st.session_state.hints):
                    # Get next hint
                    current_hint = st.session_state.hints[st.session_state.hint_count]
                    hint_type, hint_word = current_hint
                    
                    # Display only the current hint with its type
                    #st.write(f"Hint {st.session_state.hint_count + 1}/{len(st.session_state.hints)}:")
                    if hint_type == "synonym":
                        st.info(f"{hint_word}")
                    else:
                        st.success(f"{hint_word}")
                    
                    # Increment hint counter
                    st.session_state.hint_count += 1
                else:
                    st.warning("No more hints available!")
            else:
                st.write("Sorry, couldn't generate hints for this word.")
    with col5:
        if st.button("New Game"):
            reset_game()
            st.rerun()
    
    with col3:
        if st.button("Reveal Answer"):
            st.write(f"The word was: {st.session_state.target_word}")

    # Show previous guesses
    if st.session_state.previous_guesses:
        st.write("Your previous guesses:")
        for guess, score in sorted(st.session_state.previous_guesses.items(), key=lambda x: x[1]):
            st.write(f"- {guess} (Score: {score})")

else:
    st.error("No target word available for guessing. Please try refreshing the page.")