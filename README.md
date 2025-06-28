# GTI Stock Analysis API

🚀 **API phân tích chứng khoán Việt Nam**

## 🌐 Deployment

### Requirements
- Python 3.11+
- FastAPI
- Dependencies in `requirements.txt`

### Installation
```bash
pip install -r requirements.txt
python start.py
```

### API Endpoints
- `GET /` - Health check
- `GET /full-analysis/{stock_symbol}` - Stock analysis
- `GET /docs` - API documentation

### Environment Variables
- `PORT` - Server port (default: 8000)
- `ENVIRONMENT` - Environment mode (production/development)

---
**Made for Vietnamese Stock Market Analysis** 