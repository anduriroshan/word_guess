import streamlit as st
import random
import requests
import nltk
from nltk.corpus import wordnet
from nltk.corpus import brown
from difflib import SequenceMatcher
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('corpora/wordnet')
    nltk.data.find('corpora/brown')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('wordnet')
    nltk.download('brown')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('universal_tagset')

# Build word frequency dictionary from Brown corpus
word_freq = Counter(word.lower() for word in brown.words())

def get_word_complexity(word):
    """Calculate word complexity based on frequency and length"""
    freq = word_freq.get(word.lower(), 0)
    length_factor = len(word) / 10  # normalize length
    if freq == 0:
        freq_factor = 0
    else:
        freq_factor = min(1, freq / 1000)  # normalize frequency
    return 1 - ((freq_factor + (1 - length_factor)) / 2)  # 0 = simple, 1 = complex

def fetch_random_noun():
    """Fetch a random noun from the Datamuse API"""
    response = requests.get("https://api.datamuse.com/words?rel_jja=noun")
    if response.status_code == 200:
        words = response.json()
        single_word_nouns = [word['word'] for word in words if word['word'].isalpha()]
        if single_word_nouns:
            return random.choice(single_word_nouns)
    st.error("Failed to fetch noun or no suitable nouns available")
    return None

def calculate_similarity(guess, target):
    """Legacy wrapper for calculate_enhanced_similarity"""
    return calculate_enhanced_similarity(guess, target)

def calculate_enhanced_similarity(guess, target):
    """
    Calculate semantic similarity between guess and target word
    Returns a score from 0 (identical) to 1000 (completely different)
    """
    guess_synsets = wordnet.synsets(guess.lower())
    target_synsets = wordnet.synsets(target.lower())
    
    if not guess_synsets or not target_synsets:
        # Fallback to string similarity if words not in WordNet
        return 1000 - int(SequenceMatcher(None, guess.lower(), target.lower()).ratio() * 1000)
    
    # Get primary synsets
    guess_synset = guess_synsets[0]
    target_synset = target_synsets[0]
    
    # Calculate different similarity metrics
    path_sim = guess_synset.path_similarity(target_synset) or 0
    wup_sim = guess_synset.wup_similarity(target_synset) or 0
    
    # Definition similarity
    guess_def = set(guess_synset.definition().lower().split())
    target_def = set(target_synset.definition().lower().split())
    def_sim = len(guess_def.intersection(target_def)) / max(len(guess_def.union(target_def)), 1)
    
    # Usage example similarity
    guess_examples = set(" ".join(guess_synset.examples()).lower().split()) if guess_synset.examples() else set()
    target_examples = set(" ".join(target_synset.examples()).lower().split()) if target_synset.examples() else set()
    usage_sim = len(guess_examples.intersection(target_examples)) / max(len(guess_examples.union(target_examples)), 1) if guess_examples and target_examples else 0
    
    # Combine similarities with weights
    combined_sim = (
        path_sim * 0.3 +      # Path similarity weight
        wup_sim * 0.3 +       # Wu-Palmer similarity weight
        def_sim * 0.2 +       # Definition similarity weight
        usage_sim * 0.2       # Usage context similarity weight
    )
    
    return int((1 - combined_sim) * 1000)

def get_semantic_hints(word):
    """Legacy wrapper for get_enhanced_semantic_hints"""
    return get_enhanced_semantic_hints(word)

def get_enhanced_semantic_hints(word):
    """Generate semantic hints for the target word"""
    hints = []
    synsets = wordnet.synsets(word)
    
    if not synsets:
        return hints
    
    primary_synset = synsets[0]
    
    # 1. Get synonyms with complexity rating
    lemmas = primary_synset.lemmas()
    for lemma in lemmas:
        synonym = lemma.name()
        if synonym != word and len(synonym) > 2:
            complexity = get_word_complexity(synonym)
            if complexity < 0.7:  # Only use relatively common synonyms
                hints.append(("synonym", f"Similar word: {synonym}"))
    
    # 2. Get hypernyms (categories)
    hypernym_paths = primary_synset.hypernym_paths()
    for path in hypernym_paths:
        for hypernym in path[-3:]:  # Get last 3 levels of hierarchy
            for lemma in hypernym.lemmas():
                if lemma.name() != word and len(lemma.name()) > 2:
                    hints.append(("category", f"Type of: {lemma.name()}"))
    
    # 3. Add definitional hints
    definition = primary_synset.definition()
    def_words = definition.split()
    if len(def_words) > 3:
        key_words = [w for w in def_words if len(w) > 3 and w.lower() not in {'the', 'and', 'or', 'a', 'an', 'in', 'of', 'to', 'for'}]
        if key_words:
            hint_phrase = " ".join(random.sample(key_words, min(3, len(key_words))))
            hints.append(("definition", f"Definition contains: {hint_phrase}"))
    
    # 4. Add usage example hints
    examples = primary_synset.examples()
    if examples:
        example = random.choice(examples)
        masked_example = example.replace(word, "___").replace(word.capitalize(), "___")
        hints.append(("usage", f"Used in: {masked_example}"))
    
    # 5. Add domain categories
    if hasattr(primary_synset, 'topic_domains') and primary_synset.topic_domains():
        for domain in primary_synset.topic_domains():
            hints.append(("domain", f"Related to: {domain.name().split('.')[0]}"))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_hints = []
    for hint in hints:
        if hint[1] not in seen:
            seen.add(hint[1])
            unique_hints.append(hint)
    
    # Shuffle and interleave different hint types
    random.shuffle(unique_hints)
    return unique_hints

# Initialize session state
def init_session_state():
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
    """Reset all game state variables"""
    st.session_state.target_word = fetch_random_noun()
    st.session_state.game_over = False
    st.session_state.previous_guesses = {}
    st.session_state.hints = []
    st.session_state.used_hints = []
    st.session_state.hint_count = 0

def main():
    """Main game interface"""
    st.title("Word Guesser Game")
    init_session_state()

    if st.session_state.target_word:
        st.write("Try to guess the word!")
        
        # Guess input form
        with st.form(key='guess_form'):
            user_guess = st.text_input("Enter your guess:", key="guess_input")
            submit_guess = st.form_submit_button("Submit Guess")
        
        # Process guess
        if submit_guess and user_guess:
            if user_guess.lower() in st.session_state.previous_guesses:
                st.warning(f"You've already guessed '{user_guess}'! Try a different word.")
            elif not st.session_state.game_over:
                similarity_score = calculate_enhanced_similarity(user_guess, st.session_state.target_word)
                st.session_state.previous_guesses[user_guess.lower()] = similarity_score
                
                st.write(f"You are {similarity_score} units away from the answer.")
                
                if similarity_score == 0:
                    st.success(f"🎉 Correct! The word was '{st.session_state.target_word}'")
                    st.session_state.game_over = True
                elif similarity_score <= 20:
                    st.warning("Almost there!")
                elif similarity_score <= 200:
                    st.warning("Very close! Try a similar word!")
                elif similarity_score <= 500:
                    st.info("You're getting warmer!")
                else:
                    st.write("Not quite, keep trying!")

        # Game controls
        col1, col2, col3, _, col5 = st.columns(5)
        with col1:
            if st.button("Get Hint"):
                if not st.session_state.hints:
                    st.session_state.hints = get_enhanced_semantic_hints(st.session_state.target_word)
                
                if st.session_state.hints:
                    if st.session_state.hint_count < len(st.session_state.hints):
                        hint_type, hint_text = st.session_state.hints[st.session_state.hint_count]
                        if hint_type == "synonym":
                            st.info(hint_text)
                        else:
                            st.success(hint_text)
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

        # Display previous guesses
        if st.session_state.previous_guesses:
            st.write("Your previous guesses:")
            for guess, score in sorted(st.session_state.previous_guesses.items(), key=lambda x: x[1]):
                st.write(f"- {guess} (Score: {score})")

    else:
        st.error("No target word available for guessing. Please try refreshing the page.")

if __name__ == "__main__":
    main()