# TuneLink_08

TuneLink is a web based forum that integrates with Spotify to help users find people through their shared music interests. The application is built using Flask, Spotipy and other tools to create a pleasant user experience. 

---

## Features

| Feature                | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **Spotify Integration** | Log in with your Spotify Account to access personalized music data.        |
| **Top Tracks/Artists**  | View your top 5 artists and tracks based on your listening habits.         |
| **Genre Insights**      | Discover the genres you listen to the most.                               |
| **User Profile**        | Display your Spotify Profile Information, including your profile picture. |

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Technologies Used](#technologies-used)
3. [Setup Instructions](#setup-instructions)
4. [Contributing](#contributing)
5. [Development Workflow](#development-workflow)
6. [FAQ](#faq)

---

## Getting Started 

### Prerequisites
1. **Python Version**: Ensure you have [Python](https://www.python.org/downloads/) 3.10 or higher installed. Check your version by running:
    ```bash
    python3 --version
    ```
    or
    ```bash
    python --version
    ```
2. **PostgreSQL:** Install [PostgreSQL](https://www.postgresql.org/download/) for database management. Ensure it is running and accessible. 
3. **Spotify Developer Account:** You need access to [Spotify Developer](https://developer.spotify.com/) credentials (client ID and client secret). Contact `nutvendor`on Discord and provide a Spotify linked email to be added as a user for API access. 
---
### Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/TuneLink_08.git
   cd TuneLink_08
   ```
2. **Set up a Virtual Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3. **Install Dependencies:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
4. **Set up Environment Variables:** Create a `.env` file in the root directory and add the following:
    ```
    FLASK_SECRET = your_flask_secret_key
    SPOTIPY_CLIENT_ID = your_spotify_client_id
    SPOTIPY_CLIENT_SECRET = your_spotify_client_secret
    SPOTIPY_REDIRECT_URI = http://127.0.0.1:5000/callback
    SPOTIPY_SCOPE = user-top-read
    DB_NAME = your_database_name
    DB_USERNAME = your_database_username
    DB_USER_PASSWORD = your_database_password
    DB_HOST = your_database_host
    DB_PORT = 5432
    ```

- Replace placeholders with your actual credentials. 
- Contact `nutvendor` on discord for Spotify Keys, also send your name and email (linked to Spotify) to be added as a user. You must be a registered user to use the API and therefore also the app. 
5. **Run the Application**:
    ```bash
    flask run
    ```
6. **Access the Application:** Open your browser and navigate to `http://127.0.0.1:5000`

## Contributing
Tunelink welcomes contributions! Please follow the [CONTRIBUTING.md](CONTRIBUTING.md) guidelines to get started. 

## Development Workflow
The project follows the **Gitflow** workflow. Use the following approach for development:
1. **Pull the latest changes:** 
Always pull the latest changes from the `dev` branch before starting to work:
    ```bash
    git checkout dev
    git pull origin dev
    ```
2. **Create a feature branch from `dev`:** 
    ```bash
    git checkout -b feature/your-feature-name
    ```
3. **Work on your feature:**
Make changes, commit regularly and push to your branch:
    ```bash
    git add .
    git commit -m "Add feature: your-feature-name"
    git push origin feature/your-feature-name
    ```
4. **Create a Pull Request (PR):**
When your feature is complete, create a pull request to the `dev` branch.
5. **Code Review:** 
Team members will review your code. Address any feedback provided before any new review request.
6. **Merge of branch:**
Once approved, your branch will be merged into `dev` and your feature branch will be deleted. 


## FAQ
**Q: What if I can't access the Spotify API?**  
A: Ensure you have contacted `nutvendor` on Discord and provided your Spotify-linked email.

**Q: How do I troubleshoot database connection issues?**  
A: Verify that your `.env` file contains the correct database credentials, otherwise contact `nutvendor` on Discord. 