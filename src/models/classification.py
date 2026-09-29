"""Classification estimator factory."""

from sklearn.tree import DecisionTreeClassifier


def create_decision_tree_classifier(
    max_depth: int | None = None, random_state: int = 42
) -> DecisionTreeClassifier:
    """Create an unfitted decision tree classifier."""
    return DecisionTreeClassifier(max_depth=max_depth, random_state=random_state)