# -*- coding: utf-8 -*-
import numpy as np
from sklearn.datasets import fetch_openml


def flylsh(data, hash_len, sampling_r, embed_size):
    """
    Fly-LSH
    :return: Fly-LSH
    """

    # Step 1: Divisive normalization
    data = data - np.mean(data, axis=1)[:, None]

    # Step 2: Random projection
    num_projections = int(
        sampling_r * data.shape[1]
    )  # number of projections from PNs to KCs
    weights = np.random.random((data.shape[1], embed_size))
    yindices = np.arange(weights.shape[1])[None, :]
    xindices = weights.argsort(axis=0)[-num_projections:, :]
    weights = np.zeros_like(weights, dtype=np.bool)
    weights[xindices, yindices] = True  # sparse projection vectors

    # Step 3: Hashing by winner-take-all
    all_activations = np.dot(data, weights)
    xindices = np.arange(data.shape[0])[:, None]
    yindices = all_activations.argsort(axis=1)[:, -hash_len:]
    hashes = np.zeros_like(all_activations, dtype=np.bool)
    hashes[xindices, yindices] = True
    return hashes


def main():
    mnist = fetch_openml("mnist_784")
    x = mnist.data[:10]
    print(x)
    hash_length = 64
    sampling_ratio = 0.10
    embedding_size = int(20 * hash_length)
    shashes = flylsh(x, hash_length, sampling_ratio, embedding_size)
    for h in shashes.tolist():
        bits = "".join(["1" if x else "0" for x in h])
        print(len(bits), bits)
        break


if __name__ == "__main__":
    main()
