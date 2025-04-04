# TuneLink_08

TuneLink is a web based forum that integrates with Spotify to help users find people through their shared music interests. The application is built using Flask, Spotipy and other tools to create a pleasent user experience. 

---

## Features
- **Spotify Integration**: Log in with your Spotify account to access personalized music data.
- **Top Tracks and Artists**: View your top 5 artists and tracks based on your listening habits. 
- **Genre Insights**: Discover the genres you listen to the most.
- **User Profile**: Display your Spotify profile information, including your profile picture and display name. 

## Table of Contents

1. [Getting Started](#getting-started)
2. [Technologies Used](#technologies-used)
3. [Setup Instructions](#setup-instructions)
4. [Usage](#usage)
5. [Development Workflow](#development-workflow)
6. [Contributing](#contributing)

---

## Getting Started 

To get started with TuneLink, follow the setup instructions below to run the application locally.
---
### Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/TuneLink_08.git
   cd TuneLink_08
2. **Set up a Virtual Environment:**
    python3 -m venv .venv
    source .venv/bin/activate
3. **Install Dependencies:**
    pip install -r requirements.txt
4. **Set up Environment Variables:** Create a `.env` file in the root directory and add the following:
    FLASK_SECRET=your_flask_secret_key
    SPOTIPY_CLIENT_ID=your_spotify_client_id
    SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
    SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/callback
    SPOTIPY_SCOPE=user-top-read
5. **Run the Application**:
    flask run

6. **Access the Application:** Open your browser and navigate to `http://127.0.0.1:5000`

## Usage
1. Log in with your Spotify account.
2. View your top tracks, artists and genres on your profile page.
3. Explore your personalized music insights

## Development Workflow
The project follows the **Gitflow** workflow:
1. Create a feature branch from `dev`: 
    git checkout -b feature/your-feature-name
2. Commit and push changes reguearly:
    git add .
    git commit -m "Add feature: your-feature-name"
    git push origin feature/your-feature-name
3. Create a pull request to `dev` when the feature is complete.
4. Merge the feature branch into `dev` after approval.

For more details, see the [CONTRIBUTING.md](/CONTRIBUTING.md) file. 

