"""Utility functions for cosine similarity calculations."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def embedding_cosine_similarity(websites):
    """Compute cosine similarity between websites."""
    # Extract the titles from websites
    titles = [w["title"] for w in websites]

    # Convert text into numerical TF-IDF(Term Frequency - Inverse Document Frequency) vectors
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(titles)

    # Compute cosine similarity between all website vectors
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    results = []
    # Compare each website with every other website (avoid duplicates)
    for i in range(len(websites)):
        for j in range(i + 1, len(websites)):
            score = similarity_matrix[i, j]
            if 0.4 < score < 1:
                results.append((websites[i]["url"], websites[j]["url"], score))
    return results
