# Contributing to TruthLens

Thank you for your interest in contributing!

## How to contribute

### Reporting bugs
Open an issue on GitHub with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your OS and Python version

### Suggesting features
Open an issue with the `enhancement` label and describe what you'd like to see.

### Submitting code

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest tests/ -k "not integration"`
5. Commit: `git commit -m "Add your feature"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

## Development setup

```bash
git clone https://github.com/YOURUSERNAME/truthlens
cd truthlens
pip install -r requirements.txt
pip install pytest
pytest tests/ -k "not integration"
```

## Areas we need help with

- More LLM provider adapters (Cohere, Mistral API, etc.)
- Better hallucination detection prompts
- Evaluation datasets for benchmarking
- Chrome extension improvements
- Documentation and tutorials
- Research paper contributions

## Code style

- Python: follow PEP 8, use type hints
- JavaScript: standard ES6+
- Keep functions focused and small
- Add docstrings to public functions
- Write tests for new features

## License

By contributing, you agree your contributions will be licensed under the MIT License.
