# retime

Retime allows you to rewrite your Hackatime project's heartbeats if an editor
extension has messed up project detection.

Use the BEARER_TOKEN environment variable to supply a token.

## how

```sh
pipx install git+https://github.com/iamawatermelo/retime
BEARER_TOKEN=... retime fetch <date to fetch heartbeats from> <optional date to fetch heartbeats until>
BEARER_TOKEN=... retime resend <project name> <absolute root directory of your project>
```

For example:
```sh
retime fetch 2025-01-05
retime resend "dawn" "/home/sarah/Documents/dawn"
```