import openai
import re
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Set up OpenAI API credentials
load_dotenv()
openai.api_key = os.getenv("GITHUB_API_KEY")


def extract_url(user_url):
    pattern = r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)"
    match = re.search(pattern, user_url)
    if match:
        return match.group(0)
    else:
        return None


def get_user_repositories(username):
    # Fetch the repositories for the given GitHub username
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def assess_complexity(description):
    # Assess the complexity based on the repository description
    if description is None:
        return 0
    else:
        return len(description)


def generate_analysis(repo_name):
    # Generate analysis justification using GPT-3
    prompt = f"Analyzing repository {repo_name}."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": "Why is this repository technically challenging?",
            },
        ],
    )
    analysis = response.choices[0].message.content
    return analysis


@app.route("/")
def index():
    # Render the index.html template
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_repository():
    # Handle the repository analysis request
    user_url = request.form.get("userUrl")

    username = user_url.split("/")[-1] if user_url else None
    if username:
        repositories = get_user_repositories(username)
        if repositories is not None:
            most_complex_repo = None
            max_complexity_score = 0

            for repo in repositories:
                description = repo.get("description", "")
                complexity_score = assess_complexity(description)

                if complexity_score > max_complexity_score:
                    max_complexity_score = complexity_score
                    most_complex_repo = repo

            if most_complex_repo:
                repo_name = most_complex_repo.get("name")
                repo_url = most_complex_repo.get("html_url")
                if repo_name and repo_url:
                    analysis = generate_analysis(repo_name)
                    return render_template(
                        "index.html",
                        result=repo_name,
                        repo_url=repo_url,
                        analysis=analysis,
                    )
                else:
                    return render_template(
                        "index.html", error="Failed to retrieve repository information."
                    )
            else:
                return render_template("index.html", error="No repositories found.")
        else:
            return render_template("index.html", error="Failed to fetch repositories.")
    else:
        return render_template("index.html", error="Invalid GitHub User URL.")


if __name__ == "__main__":
    app.run(debug=True)
