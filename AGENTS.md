# Things You (AI Agent) Should Know

## When Creating or Modifying Programming Code
- `uv` is available in this environment
  - Do not use the `python` or `pip` commands; use the `uv` command instead
    - To run a Python file, use: `uv run --env-file .env filename other_arguments`
    - For lint checks, use: `uv run ruff check filename`
    - For type checking, use: `uv run basedpyright filename`

- Do not install packages
  - If you need to use something that is not installed,
    - Ask me to install it
    - Or use it in a way that disappears automatically when the session ends

- First, create a detailed coding plan
  - Basically, use Python's standard modules
  - When using non-standard modules, list them at the planning stage
  - Once the plan is complete, do not start implementation immediately; always consult with me (the user) about the plan first

- Code the program based on the plan
  - Use environment variables
    - Use the `.env` file
    - Example of env usage:
      ```python
      import os

      def get_api_key(api_key: str | None = None) -> str | None:
        if api_key is None:
          api_key = os.getenv("API_KEY")
        return api_key

      api_key = get_api_key(api_key)
      ```
  - Code must comply with Ruff linting (refer to `pyproject.toml`)

- Once the code is complete
  - Check for errors with Ruff and basedpyright
