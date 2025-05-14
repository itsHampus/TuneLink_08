# Contributing to TuneLink_08

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Bucket Releases](#bucket-releases)
4. [Code Review Process](#code-review-process)
5. [Coding Standards](#coding-standards)
6. [Hotfixes](#hotfixes)
<!-- 7.[Testing](#testing)  -->

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



## Development Workflow
# Development Workflow
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

## Bucket Releases
At the end of each sprint, completed features in `dev` are collected and merged into `main` as part of a **bucket release**. Follow these steps:

1. Perform final testing of the `dev` branch.
2. Fix any bugs before merging into `main`. 
3. Create a pull request (PR) from `dev`to `main`.
4. At least one team member should review the code. 
5. Once the PR is approved, merge `dev` into `main`.
6. Tag the release with a version number and document changes in the changelog:
    ```bash
    git tag -a vX.X.X -m "Release vX.X.X"
    git push origin vX.X.X
    ```

## Code Review Process
The project uses a **peer review process** to ensure code quality. All pull requests must:
- Be reviewed by at least one team member (preferably two for bucket releases).
- Pass all automated tests and checks (e.g `pytest`, `flake8`, `black` and `isort`).
- Include clear and descriptive commit messages.

## Coding Standards
1. Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code style. 
- Use `flake8` to check for code style violations:
    ```bash
    flake8 .
    ```
- Use `black` for automatic code formatting across the project:
    ```bash
    black .
    ```
2. Use type annotations where applicable.
3. Write meaningful docstrings for all functions and classes using the **Google style** or **PEP 257**
4. Organize imports using `isort`:
    ```bash
    isort .
    ```



<!-- ## Testing 
1. Write unit tests for all new features or bug fixes. 
2. Place test files in the `tests/` directory.
3. Run tests locally before submitting a pull request:
    ```bash
    pytest -->


## Hotfixes
If a critical bug is discovered in `main`, follow these instructions:
1. Create a temporary hotfix branch directly from `main`:
    ```bash
    git checkout main
    git checkout -b hotfix/critical-bug
    ```
2. Fix the bug and commit the changes.
3. Merge the hotfix branch into both `main` and `dev`:
    ```bash
    git checkout main
    git merge hotfix/critical-bug
    git checkout dev
    git merge hotfix/critical-bug
    ```
4. Push the changes to the repository:
    ```bash
    git push origin main
    git push origin dev  
    ```  
