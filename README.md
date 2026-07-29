<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/krishnaUIDev/krishnaUIDev/main/dark_mode.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/krishnaUIDev/krishnaUIDev/main/light_mode.svg">
    <img alt="Krishna Kondoju's GitHub Stats" src="https://raw.githubusercontent.com/krishnaUIDev/krishnaUIDev/main/dark_mode.svg" width="100%">
  </picture>
</div>

---

### ⚙️ How It Works

This profile README automatically updates daily using **GitHub Actions** and **GitHub GraphQL API**.

* **`today.py`**: Fetches real-time repositories, stars, followers, and contributions.
* **`ascii_converter.py`**: Converts your GitHub avatar picture into dynamic ASCII text art.
* **Theme Support**: Renders `dark_mode.svg` or `light_mode.svg` automatically based on your viewer's GitHub theme choice.

---

### 🚀 Setup Instructions for Your Profile

1. Create a public repository named `<your-github-username>` (e.g. `krishnaUIDev/krishnaUIDev`).
2. Push this repository code to `main`.
3. Go to **Settings > Secrets and variables > Actions** in your repository.
4. Add a **New repository secret**:
   * **Name**: `ACCESS_TOKEN`
   * **Value**: A GitHub Personal Access Token (PAT) with `read:user`, `read:org`, `repo` scopes.
5. (Optional) Add environment secret `BIRTHDAY` with value `YYYY-MM-DD` if you want an age ticker.
6. The action will run automatically every day at 04:00 UTC!
