# GitHub Contribution Workflow (Fork-Based)

Before following this workflow please refer to our [**New Contributor Guide**](./new_contributor_guide.md) page for instructions on installing dependencies and setting up your development environment.

## Overview

All changes should be made in a forked repository, submitted via pull request to the upstream `develop` branch, and later merged into `main` for a new release.


## Opening a Pull Request (PR)

1. **Fork the repository**   

    - Navigate to the [main repository](https://www.github.com/civictechdc/cib-mango-tree) on GitHub.
    - Click the **Fork** button in the upper right corner.
    - This creates a copy of the repository under your GitHub account.

2. **Clone your fork**  

      Clone your forked repository to your local machine:

      ```shell
      git clone https://github.com/YOUR-USERNAME/REPOSITORY-NAME.git
      cd REPOSITORY-NAME
      ```

3. **Add upstream remote**

      Add the original repository and name it as `upstream` remote:

      ```shell
      git remote add upstream https://github.com/ORIGINAL-OWNER/REPOSITORY-NAME.git
      git remote -v
      ```

4. **Create a feature branch**

      Branch from `develop` using `feature/<name>` or `bugfix/<name>`:

      ```shell
      git checkout develop
      git pull upstream develop
      git checkout -b feature/new-feature
      ```

5. **Make changes & push to fork**

    - Commit changes with clear messages.
    - Push the branch to your forked repository.

      ```shell
      git add .  # adds changes in all non-ignored files in current folder
      git commit -m "Description of changes"
      git push origin feature/new-feature
      ```

6. **Create a pull request**

    - Navigate to the original repository on GitHub.
    - Click **Pull requests** > **New pull request**.
    - Click **compare across forks**.
    - Set the base repository to `ORIGINAL-OWNER/REPOSITORY-NAME` and base branch to `develop`.
    - Set the head repository to `YOUR-USERNAME/REPOSITORY-NAME` and compare branch to `feature/new-feature`.
    - Click **Create pull request** and fill in the details.
    - Address any review feedback.

7. **Keep your fork updated**   

      Regularly sync your fork with the upstream repository:

      ```shell
      git checkout develop
      git pull upstream develop
      git push origin develop
      ```

8. **After merge & clean up**

    - After your PR is approved and merged into upstream `develop`, delete your feature branch:

      ```shell
      git checkout develop
      git branch -d feature/new-feature
      git push origin --delete feature/new-feature
      ```

9. Release

      - When `develop` is clean and ready for a new major release, maintainers will merge `develop` into `main`.

