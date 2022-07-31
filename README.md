# podman-compose additional tools

**This repo is currently in heavy development! Do not use in production!**

## podman-compose backup

This will become a tool helping with backing up & restoring volume's contents of compose setups.
Sane defaults will allow usage on common compose setups without adaption.
However many configuration settings will allow to improve the backups, e.g. by backing up MySQL/MariaDB databases using `mysqldump`.
See [this compose file](./example/compose.yml) as an example usage.

This tool requires to only

This will enable server administrators to easily implement resilient backups (used together with tools storing the output of this tool).
It will also allow to easily migrate compose setups from one to another system.

In future, I may implement another tool to allow auto-updates with extended service testing (e.g. testing home page),
which uses this implementation to create a snapshot to rollback to in case of an error.

## License

This repository is licensed under GNU AGPL 3.0.
You find a copy of the license terms in [LICENSE](./LICENSE)
