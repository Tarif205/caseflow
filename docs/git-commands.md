# Git commands for this project

The commands this project needs, grouped by when you use them.

## First push

| Command | What it does |
|---|---|
| `git status` | Shows what is changed, staged or untracked. Run it before and after everything. |
| `git add .` | Stages all changes in the folder for the next commit. |
| `git add <file>` | Stages one file only. |
| `git commit -m "message"` | Saves the staged changes as a commit with that message. |
| `git remote add origin <url>` | Names your GitHub repo `origin` so you can push to it. |
| `git remote -v` | Lists the remotes and their URLs. |
| `git push -u origin main` | Uploads `main` and links it to GitHub. After this once, plain `git push` is enough. |

## One-time setup

| Command | What it does |
|---|---|
| `git config --global user.name "Your Name"` | Sets the author name on your commits. |
| `git config --global user.email "you@example.com"` | Sets the author email (public in every commit). |
| `git init -b main` | Turns a folder into a repository. |
| `git clone <url>` | Downloads an existing repository to a new folder. |

## Daily work

| Command | What it does |
|---|---|
| `git diff` | Shows unstaged changes line by line. |
| `git diff --staged` | Shows what the next commit will contain. |
| `git log --oneline` | Lists past commits, one line each. |
| `git pull` | Downloads and merges new commits from GitHub. |
| `git push` | Uploads your new commits. |
| `git mv <old> <new>` | Moves or renames a file and stages the change. |
| `git rm --cached <file>` | Stops tracking a file but keeps it on disk (for a file you committed by mistake). |

## Branches (one per sprint)

| Command | What it does |
|---|---|
| `git branch` | Lists branches; the current one has a `*`. |
| `git switch -c sprint-1` | Creates a branch and moves to it. |
| `git switch main` | Moves back to `main`. |
| `git merge sprint-1` | Merges that branch into the one you are on. |
| `git branch -d sprint-1` | Deletes a branch that is already merged. |

## Undoing

| Command | What it does |
|---|---|
| `git restore <file>` | Throws away unstaged changes in that file. This cannot be undone. |
| `git restore --staged <file>` | Unstages a file but keeps your changes. |
| `git commit --amend -m "new message"` | Rewrites the last commit. Only use it before you push. |
| `git revert <commit>` | Makes a new commit that undoes an old one. Safe after pushing. |
