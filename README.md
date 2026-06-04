# Flashcard Quiz App
Create decks, add cards, quiz yourself with difficulty tracking

## Live Demos
| Version | Link |
|---|---|
| Frontend Only (Netlify) | [View Live](https://flash-cards-game5.netlify.app) |
| Full-Stack with Backend | *Add Render link after deploying* |

## Built With
Python · Flask · SQLite · HTML · CSS · JavaScript

## Run Locally
```
pip install -r requirements.txt
python app.py
```

## Deploy on Render
1. Push this folder to a GitHub repo
2. Go to render.com → New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
