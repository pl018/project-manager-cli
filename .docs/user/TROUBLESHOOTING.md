# Troubleshooting

## Common issues

- **Permission denied**
  - Ensure the directories for the database and `projects.json` are writable.
  - Run `pm-cli config` to see current paths.

- **Cursor `projects.json` not found**
  - Verify Cursor is installed and has created the Project Manager storage.
  - Path usually is `%APPDATA%/Cursor/User/globalStorage/alefragnani.project-manager/projects.json`.
  - Override with `PROJECT_MANAGER_PROJECTS_FILE` if needed.

- **AI errors or timeouts**
  - Check `OPENAI_API_KEY` is set and valid.
  - Try `--skip-ai-tags` to bypass AI.
  - Review the per-project log file for request/response details.

- **Tags rendered as characters in receipt**
  - Fixed in current code: tags are handled as lists or decoded JSON.
  - Update to latest code if still observed.

- **Property vs path errors**
  - Ensure you’re on a version where services import the config instance: `from ..config import config as Config`.

## Getting logs

After a run, the log file path is printed. It’s also located under:

```
%APPDATA%/project-manager-cli/logs/<uuid>.log
```

## Resetting configuration

```bash
pm-cli reset
pm-cli init
```


