# Bot MD5 Python - Brain Self Evolution

## Chay local
pip install -r requirements.txt
export MD5_API_TOKEN=your_token
python main.py

## Deploy Railway
1. Push len GitHub
2. Railway -> New Project -> Deploy from GitHub
3. Variables:
   - MD5_API_TOKEN = token API
   - AUTO_GIT_PUSH = true (neu muon Brain tu push)

## API
- GET /              trang thai + brain stats
- GET /api/bot/status  du doan hien tai
- GET /api/bot/brain   thong ke algorithm
