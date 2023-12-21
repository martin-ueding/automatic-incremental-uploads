import argparse
import pathlib
import tomllib

import inotify.adapters
import inotify.constants
import paramiko
import pysftp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", type=pathlib.Path)
    options = parser.parse_args()

    with open(options.config_path, "rb") as f:
        config = tomllib.load(f)

    local_basedir = pathlib.Path(config["files"]["local_basedir"])
    remote_basedir = pathlib.Path(config["files"]["remote_basedir"])
    include = pathlib.Path(config["files"]["include"])

    watcher = inotify.adapters.InotifyTree(
        str(local_basedir / include),
        mask=inotify.constants.IN_MODIFY | inotify.constants.IN_CREATE,
    )

    agent = paramiko.Agent()
    for key in agent.get_keys():
        if key.get_name() == config["agent"]["name"]:
            agent_key = key

    print("Watches established.")
    with pysftp.Connection(
        cnopts=pysftp.CnOpts(
            **config["cn_opts"],
        ),
        private_key=agent_key,
        **config["server"],
    ) as sftp:
        print("SFTP connection established.")
        for _, event_types, path, filename in watcher.event_gen(yield_nones=False):
            file_path = pathlib.Path(path) / filename
            if not file_path.exists():
                continue

            relpath = file_path.relative_to(local_basedir)
            print(f"{file_path = }, {event_types = }, {relpath = }")

            print(f"Changing into {relpath.parent = }")
            with sftp.cd(str(relpath.parent)):
                if file_path.exists():
                    print(f"Uploading file {relpath = }")
                    sftp.put(relpath)
                    print("Done with upload.")
            print("Back in directory.")


if __name__ == "__main__":
    main()
