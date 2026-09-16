import faiss
import numpy as np

# Three example vectors
embeddings = np.array([
    [0.1, 0.2, 0.3, 0.4],  # Vector 1
    [0.2, 0.3, 0.4, 0.5],  # Vector 2
    [0.9, 0.8, 0.7, 0.6]   # Vector 3
], dtype="float32")

# Create FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)

# Add vectors
index.add(embeddings)

print("Vectors stored:", index.ntotal)


# A new question vector
query_vector = np.array([
    [0.15, 0.25, 0.35, 0.45]
], dtype="float32")


# Search for the 2 closest vectors
distances, indices = index.search(query_vector, 2)

print("\nClosest vectors:")
print(indices)

print("\nDistances:")
print(distances)