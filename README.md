# NSFW Detector

Telegram moderation bot that evaluates user profile images and removes non-admin members when explicit content exceeds a configurable threshold.

## How It Works

1. The bot reacts when a member joins or produces a visible reaction event.
2. It downloads the user's latest profile image.
3. A Transformers image-classification pipeline runs `Marqo/nsfw-image-detection-384`.
4. Scores for explicit-content labels are aggregated.
5. The user is banned when the maximum blocked-label score meets `NSFW_THRESHOLD`.

Private-chat image uploads can be used to inspect a classification result without moderating a group.

## Stack

- Python and aiogram
- Hugging Face Transformers
- PyTorch and Pillow

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

The model is downloaded by Transformers on first use and may take several minutes.

## Safety Notes

- Classification is probabilistic; tune the threshold and review false positives before production use.
- Administrator accounts are excluded from automated bans.
- Do not store or commit downloaded profile images.
- Never commit the Telegram bot token or model cache.
