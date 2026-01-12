# 🇹🇭 Thai-Chinese TTS Web App 🇨🇳

A web application that translates Thai text to Chinese and generates speech using **MeloTTS**.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

## ✨ Features

- **Hybrid Translation**: Uses `googletrans` (fast) with `deep-translator` fallback (reliable)
- **Text-to-Speech**: High-quality **MeloTTS** with adjustable speech speed
- **Modern UI**: Clean, responsive web interface
- **Docker Ready**: Run anywhere without environment setup

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Theme-P/TTS-Web-App-2.git
cd TTS-Web-App-2

# Build and run
docker-compose up --build
```

Open http://localhost:5000 in your browser.

### Local Development

```bash
# Clone the repository
git clone https://github.com/Theme-P/TTS-Web-App-2.git
cd TTS-Web-App-2

# Install dependencies
pip install -r requirements.txt
python -m unidic download

# Run the application
python app.py
```

## 📁 Project Structure

```
TTS-Web-App-2/
├── app.py                  # Flask application
├── translation_service.py  # Hybrid translation logic
├── melo_tts_service.py     # MeloTTS integration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Service orchestration
├── templates/
│   └── index.html          # Main UI template
└── static/
    ├── style.css           # Styling
    └── script.js           # Frontend logic
```

## 🔧 Configuration

### Speech Parameters
- **Speed**: Adjustable from 0.5x to 2.0x (Default: 1.0)

## 🐳 Docker Hub

Pull the pre-built image:

```bash
docker pull n301ix/tts-webapp:latest
docker run -p 5000:5000 n301ix/tts-webapp:latest
```

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/api/convert` | POST | Convert Thai text to Chinese speech |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.
