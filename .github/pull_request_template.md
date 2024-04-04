- [ ] Update PR Title to follow this pattern: `[INTENT]:[MESSAGE]`
  > The title will become a one-line commit message in the git log, so be as concise and specific as possible -- refer to [How to Write a Git Commit Message](https://cbea.ms/git-commit/). Prepend [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/#summary) intent (`fix:`, `feat:`, `chore:`, `ci:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`).

## Ticket

Resolves #{TICKET NUMBER or URL or description} or Adds {new capability or feature}


## Changes

> What was added, updated, or removed in this PR.
> Prefer small PRs; try to limit to 300 lines of code changes
> * https://blog.logrocket.com/using-stacked-pull-requests-in-github/
> * https://opensource.com/article/18/6/anatomy-perfect-pull-request
> * https://developers.google.com/blockly/guides/modify/contribute/write_a_good_pr


## Context for reviewers

> Background context, more in-depth details of the implementation, and anything else you'd like to call out or ask reviewers.
> Add comments to your code under the "Files Changed" tab to explain complex logic or code
> * https://betterprogramming.pub/how-to-make-a-perfect-pull-request-3578fb4c112


## Testing

Testing instructions and expected behavior:
1. `pip install -r requirements.txt`
1. Update `.env`
1. Start openhermes LLM using Ollama: `ollama run openhermes` (Install Ollama from https://ollama.ai/)

