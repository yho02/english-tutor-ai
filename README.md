# Adaptive Grammar Feedback System for L2 Learners

### Prerequisites

- Python 3.8 or higher
- pip (comes with Python)
- A [Groq API key](https://console.groq.com) — sign up for free

To check your Python version:
```
python --version
```

### Installing

1. Clone the repository

```
git clone https://github.com/your-username/english-tutor-ai.git
cd english-tutor-ai
```

2. Create and activate a virtual environment

```
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Add your Groq API key

Create a `.env` file in the root folder:

```
GROQ_API_KEY=your_api_key_here
```

5. Run the app

```
streamlit run main.py
```

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

