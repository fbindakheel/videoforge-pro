# Contributing to VideoForge Pro

Thanks for your interest in contributing! 🎬

## How to Contribute

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/videoforge-pro.git
   cd videoforge-pro
   ```
3. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/my-new-feature
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Make your changes** and test them:
   ```bash
   python main.py
   ```
6. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add XYZ feature"
   ```
7. **Push** to your fork and open a **Pull Request**

## Code Style

- Follow existing code structure and naming conventions
- Add docstrings to new functions/classes
- Keep UI code in `app/ui/`, processing logic in `app/core/`
- No external dependencies beyond those in `requirements.txt`

## Reporting Bugs

Open an [Issue](../../issues) with:
- Steps to reproduce
- Expected vs actual behavior
- FFmpeg version (`ffmpeg -version`)
- OS and Python version

## Feature Requests

Open an [Issue](../../issues) with the label `enhancement`. Include a clear description of:
- What you want to do
- Why it would be useful
- Any FFmpeg commands that could power it
