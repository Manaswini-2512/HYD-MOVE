"""Clustering estimator factory."""

from sklearn.cluster import KMeans


def create_kmeans_model(n_clusters: int, random_state: int = 42) -> KMeans:
    """Create an unfitted K-means estimator.

    Raises:
        ValueError: If ``n_clusters`` is not positive.
    """
    if n_clusters < 1:
        raise ValueError("n_clusters must be at least 1")
    return KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")