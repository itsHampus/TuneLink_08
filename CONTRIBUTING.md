# Contributing to TuneLink_08

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Bucket Releases](#bucket-releases)
4. [Code Review Process](#code-review-process)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Hotfixes](#hotfixes)

## Getting Started

1. **Fork the repository to your Github**
2. **Clone your forked repository**:
    ```bash
    git clone https://github.com/<your-username>/TuneLink_08.git
3. **Set up the virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
4. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
5. **Set up Environment Variables**: Create a `.env` file in the root directory and add the following:
    - FLASK_SECRET=your_flask_secret_key 
    - SPOTIPY_CLIENT_ID=contact_nutvendor_on_discord 
    - SPOTIPY_CLIENT_SECRET=contact_nutvendor_on_discord
    - SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/callback
    - SPOTIPY_SCOPE=user-top-read
Contact `nutvendor` on discord for Spotify keys, also send your name and email (linked to Spotify) to be added as a user. You must be a registered user to use the API and therefore also the app. 
6. **Install dependecies**:
    ```bash
    pip install -r requirements.txt


## Development Workflow
The project follows the Gitflow workflow. Use the following approach for development:

1. Pull the latest changes:
Always pull the latest changes from the `dev` branch before starting to work:
    ```bash
    git checkout dev
    git pull origin dev

2. Create a feature branch from `dev` with a descriptive name:
    ```bash
    git checkout -b feature/your-feature-name

3. Work in the branch, reguarly commiting and pushing changes:
    ```bash
    git add .
    git commit -m "Add feature: your-feature-name"
    git push origin feature/your-feature-name

4. When a feature is complete, create a pull request (PR) to dev.
5. Team members will review the code and test the functionality. 
6. Once the PR is approved, merge the feature into dev. 
7. Delete the feature branch if it is no longer needed:
    ```bash
    git branch -d feature/your-feature-name


## Bucket Releases
At the end of each sprint, the completed features in `dev` are collected and merged into `main` as part of a **bucket release**. Follow these steps:

1. Perform final testing of the `dev` branch.
2. Fix any bugs before merging into `main`. 
3. Create a pull request (PR) from `dev`to `main`.
4. At least one team member should review the code. 
5. Once the PR is approved, merge `dev` into `main`.
6. Tag the release with a version number and document changes in the changelog:
    ```bash
    git tag -a vX.X.X -m "Release vX.X.X"
    git push origin vX.X.X

## Code Review Process
The project uses a **peer review process** to ensure code quality. All pull requests must:
- Be reviewed by at least one team member (prefereably two for bucket releases).
- Pass all automated tests and checks (e.g `pytest`, `flake8`, `black` and `isort`).
- Include clear and descriptive commit messages.

## Coding Standards
1. Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code style. 
- Use flake8 to check for code style violations:
    ```bash
    flake8 .
- Use black for automatic code formatting across the project:
    ```bash
    black .
2. Use type annotations where applicable.
3. Write meaningful docstrings for all functions and classes using the **Google style** or **PEP 257**
4. Organize imports using `isort`:
    ```bash
    isort .



## Testing 
1. Write unit tests for all new features or bug fixes. 
2. Place test files in the `tests/` directory.
3. Run tests locally before submitting a pull request:
    ```bash
    pytest


## Hotfixes
If a critical bug is discovered in `main`, follow these instructions:
1. Create a temporary hotfix branch directly from `main`:
    ```bash
    git checkout main
    git checkout -b hotfix/critical-bug
2. Fix the bug and commit the changes.
3. Merge the hotfix branch into both `main` and `dev`:
    ```bash
    git checkout main
    git merge hotfix/critical-bug
    git checkout dev
    git merge hotfix/critical-bug
4. Push the changes to the repository:
    ```bash
    git push origin main
    git push origin dev    
