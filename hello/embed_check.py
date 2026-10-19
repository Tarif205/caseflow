"""Day 0 hello-world check 2: embed three sentences and compare them."""

import numpy as np
from fastembed import TextEmbedding

# Keep the downloaded model on G: so it survives temp-folder cleanups.
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=r"G:\fastembed-cache")

sentences = [
    "How do I return an item?",
    "What is your refund policy?",
    "The weather is sunny today.",
]

vectors = list(model.embed(sentences))
print(f"Each sentence became {len(vectors[0])} numbers.")
print(f"First 5 numbers of sentence 1: {np.round(vectors[0][:5], 3)}")


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


print()
for i in range(len(sentences)):
    for j in range(i + 1, len(sentences)):
        score = cosine(vectors[i], vectors[j])
        print(f"{score:.3f}  {sentences[i]!r} vs {sentences[j]!r}")
