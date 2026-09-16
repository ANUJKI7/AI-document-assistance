from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "Python is used for artificial intelligence.",
    "Python is a popular programming language for AI.",
    "I like eating pizza."
]

# Convert sentences into vectors
embeddings = model.encode(sentences)

# Compare sentence 1 with sentence 2
similarity_1_2 = cosine_similarity(
    [embeddings[0]],
    [embeddings[1]]
)[0][0]

# Compare sentence 1 with sentence 3
similarity_1_3 = cosine_similarity(
    [embeddings[0]],
    [embeddings[2]]
)[0][0]

print("Similarity between sentence 1 and 2:")
print(similarity_1_2)

print("\nSimilarity between sentence 1 and 3:")
print(similarity_1_3)