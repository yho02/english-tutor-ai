# English Grammar Tutor AI 
An AI-powered tool that explains grammar errors and rewrites sentences naturally

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

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
python main.py
```

You should see something like:

```
Enter a sentence: She go to school everyday.
Error: "go" should be "goes" (subject-verb agreement).
Corrected: She goes to school every day.
```

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
