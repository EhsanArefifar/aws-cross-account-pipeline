## 🚀 Pushing a Local Project to GitHub

1. **Initialize Git**

   ```bash
   git init
   ```
   Sets up version control in your local project directory.
2. **Add Files**

   ```bash
   git add .
  ```
   Stages all files for the first commit.

3. **Commit Changes**

   ```bash
   git commit -m "Initial commit"
   ```
   Records the snapshot of your project.

4. **Create a GitHub Repo**

   * Go to [github.com](https://github.com)
   * Click **New repository**
   * **Do not** initialize with README, `.gitignore`, or license
   * Create the repo

5. **Add GitHub Remote**

   ```bash
   git remote add origin https://github.com/your-username/repo-name.git
   ```
   Links your local repo to the GitHub repository.

6. **Push to GitHub**

   ```bash
   git push -u origin main
   ```
   Pushes your code to the main branch on GitHub.

✅ Your project is now version-controlled and hosted on GitHub.
