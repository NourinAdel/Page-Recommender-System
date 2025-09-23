"""Parses WARC files and uploads to neo4j """
import os
import html
from warcio.archiveiterator import ArchiveIterator
from cosine_similarity_file import embedding_cosine_similarity
from neo4j_handler import Neo4jHandler

# Connect to Neo4j Aura
URI = "neo4j+ssc://ddf97a6b.databases.neo4j.io"
USERNAME = "neo4j"
PASSWORD = "GEn8zaDGXkLRiXl7ZzvfvqghPhawI2M0P-EKDSHdrD4"

try:
    # Locate WARC files
    folder_path = "warc_cache"  # Folder containing .warc.gz files
    warc_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".warc.gz")]

    websites = []

    # Extract titles & metadata from WARC files
    for filepath in warc_files:
        print(f"[INFO] Processing {filepath}")
        with open(filepath, "rb") as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type == "response":  # Only process HTTP responses
                    payload = record.content_stream().read()
                    try:
                        text = payload.decode("utf-8", errors="ignore")
                        # Look for <title> tag
                        start = text.find("<title>")
                        end = text.find("</title>")
                        if start != -1 and end != -1:
                            page_url = record.rec_headers.get_header("WARC-Target-URI")
                            timestamp = record.rec_headers.get_header("WARC-Date")

                            # Extract text inside title tags
                            title = text[start + 7:end].strip()
                            if title:
                                websites.append({
                                    "title": html.unescape(title),
                                    "url": page_url,
                                    "timestamp": timestamp
                                })

                    except Exception:
                        continue   # Skip any record that causes errors

    print(f"[INFO] Extracted {len(websites)} website titles from {len(warc_files)} files")

    if not websites:
        print("[WARNING] No titles extracted.")
        exit(0)

    # Calculate cosine similarity between titles
    similarities = embedding_cosine_similarity(websites)
    print("[INFO] Cosine similarity matrix calculated")

    # Connect and save to Neo4j
    neo = Neo4jHandler(URI, USERNAME, PASSWORD)

    # Upload websites to Neo4j in batches
    BATCH_SIZE = 100
    for batch_start in range(0, len(websites), BATCH_SIZE):
        batch = websites[batch_start:batch_start + BATCH_SIZE]
        neo.save_websites(batch)
        print(f"[INFO] Uploaded nodes {batch_start} to {batch_start + len(batch) - 1}")

    # Upload similarities in batches
    for batch_start in range(0, len(similarities), BATCH_SIZE):
        batch = similarities[batch_start:batch_start + BATCH_SIZE]
        neo.save_similarities(batch)
        print(f"[INFO] Uploaded relationship batch {batch_start} to {batch_start + len(batch) - 1}")

    print("[INFO] All nodes and relationships uploaded successfully")

except Exception as e:
    print(f"Error: {e}")
