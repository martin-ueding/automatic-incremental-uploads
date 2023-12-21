import argparse
import contextlib
import pathlib
import shutil
import tomllib
import subprocess

import inotify.adapters
import inotify.constants


@contextlib.contextmanager
def mount_remote(remote: str, local: str):
    subprocess.run(["sshfs", remote, local], check=True)
    yield
    subprocess.run(["fusermount", "-u", local], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", type=pathlib.Path)
    options = parser.parse_args()

    with open(options.config_path, "rb") as f:
        config = tomllib.load(f)

    basedir = pathlib.Path(config["files"]["basedir"])
    include = pathlib.Path(config["files"]["include"])

    watcher = inotify.adapters.InotifyTree(
        str(basedir / include),
        mask=inotify.constants.IN_MODIFY | inotify.constants.IN_CREATE,
    )

    mountpoint = pathlib.Path(config["connection"]["mountpoint"])

    print("Watches established.")
    with mount_remote(config["connection"]["remote"], str(mountpoint)):
        print("SSH FS connection established.")
        for _, event_types, path, filename in watcher.event_gen(yield_nones=False):
            source = pathlib.Path(path) / filename
            if not source.exists():
                continue

            relpath = source.relative_to(basedir)
            target = mountpoint / relpath

            try:
                print(f"Copying {source} to {target} …")
                shutil.copy2(source, target)
                print(f"Copied {source} to target.")
            except FileNotFoundError as e:
                print(f"File {source} has vanished, deleting on target.")
                target.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
