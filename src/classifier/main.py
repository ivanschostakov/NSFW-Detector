from io import BytesIO
from PIL import Image
from transformers import pipeline

from .constants import BLOCKED_LABELS
from .result import NSFWClassifierResult
from config import NSFW_THRESHOLD


classifier = pipeline(
    "image-classification",
    model="Marqo/nsfw-image-detection-384",
)


def is_nsfw(image_bytes: bytes, threshold: float = NSFW_THRESHOLD) -> NSFWClassifierResult:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    results = classifier(image)
    max_score = 0.0

    for item in results:
        label = item["label"].lower()
        score = float(item["score"])
        if any(blocked in label for blocked in BLOCKED_LABELS): max_score = max(max_score, score)

    return NSFWClassifierResult(
        nsfw=max_score >= threshold,
        max_score=max_score,
        results=results,
    )