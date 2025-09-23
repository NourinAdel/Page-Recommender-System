""" Connects between backend and frontend using Flask application """
import atexit
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from neo4j_handler import Neo4jHandler

app = Flask(__name__)

# Neo4j connection
URI = "neo4j+ssc://ddf97a6b.databases.neo4j.io"
USERNAME = "neo4j"
PASSWORD = "GEn8zaDGXkLRiXl7ZzvfvqghPhawI2M0P-EKDSHdrD4"
neo = Neo4jHandler(URI, USERNAME, PASSWORD)

def fetch_page_title(url):
    """Fetch the title of a given webpage URL"""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else url
        return title.strip()
    except Exception:
        return url

def add_and_compute_similarity(new_url):
    """ Add new URL to Neo4j and compute similarity"""
    title = fetch_page_title(new_url)

    # check if website already exists
    if neo.exists_website(new_url):
        return

    # otherwise, create website node
    neo.save_websites([{"url": new_url, "title": title, "timestamp": None}])

    # get all websites currently in DB
    websites = neo.get_all_websites()
    urls = [w["url"] for w in websites]
    titles = [w["title"] for w in websites]

    # compute vectors and cosine similarity
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(titles)
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    new_idx = urls.index(new_url)

    similarities = []

    # compare new website against all others
    for i, other_url in enumerate(urls):
        if i == new_idx:
            continue
        score = similarity_matrix[new_idx, i]
        if 0.4 < score < 1:
            similarities.append((new_url, other_url, float(score)))


    # save relationships
    neo.save_similarities(similarities)

def recommend_from_neo4j(url, top_k=5):
    """Get recommendations for a given URL"""
    if not neo.exists_website(url):
        add_and_compute_similarity(url)
    return neo.recommend_similar(url,top_k = top_k)

@app.route("/", methods=["GET", "POST"])
def index():
    """Handle user input URL and return recommendations to the frontend """
    query_url = None
    recommendations = []
    if request.method == "POST":
        # get user input (URL)
        query_url = request.form["url"]
        # get recommendations from Neo4j
        recommendations = recommend_from_neo4j(query_url)

    # render frontend with current URL and its recommendations
    return render_template("frontend.html", url=query_url, recommendations=recommendations)


atexit.register(neo.close)

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
