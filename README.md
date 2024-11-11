# Word Guesser Game
![image](https://github.com/user-attachments/assets/75458a65-3e83-4533-a847-db3d5e010392)

## Overview

The Word Guesser Game is a Streamlit-based application that challenges users to guess a randomly selected word. The game provides semantic hints and calculates the similarity between the user's guess and the target word, giving feedback to help the user converge on the correct answer.

## Features

-   Randomly selects a noun from the Datamuse API as the target word
-   Calculates the semantic similarity between the user's guess and the target word
-   Provides various types of semantic hints to assist the user, including:
    -   Synonyms
    -   Hypernyms (category information)
    -   Definition hints
    -   Usage examples
    -   Domain categories
-   Keeps track of the user's previous guesses and the similarity scores
-   Allows the user to request hints, reveal the answer, or start a new game

## Semantic Hints Generation

The application generates semantic hints using the following approach:

1.  **Synonyms**: The game retrieves synonyms of the target word from WordNet and filters them based on a complexity score (using word frequency and length). Only relatively common synonyms are included as hints.
2.  **Hypernyms (Categories)**: The game traverses the hypernym (is-a) hierarchy of the target word in WordNet, and includes the last three levels of the hierarchy as category-based hints.
3.  **Definition Hints**: The game extracts key words from the definition of the target word's primary synset in WordNet and uses them to construct a hint.
4.  **Usage Examples**: The game selects a random usage example for the target word from WordNet and masks the target word, presenting it as a usage-based hint.
5.  **Domain Categories**: If available, the game includes the topic domains associated with the target word's primary synset as additional hints.

## Semantic Similarity Scoring

The application calculates the semantic similarity between the user's guess and the target word using an enhanced version of the Wu-Palmer similarity algorithm provided by WordNet. The similarity score is normalized to a range of 0 (identical) to 1000 (completely different), and this score is used to provide feedback to the user.
