# Automatic Incremental Uploads

I often develop things on my laptop and then need to test them on a server when I program for hardware that I don't have in my laptop. For this it is nice to have automatic upload of changed files to the remote server.

The CLion/PyCharm IDE has upload functionality for SFTP built-in, it just gets stuck every now and then. There doesn't seem to be a way to get it unstuck again except for waiting like half an hour. Therefore I want to have an independent tool that does this and where I can restart just this part.

This works by setting an _inotify_ watch on a directory tree. Whenever there are changes it will propagate these changes to the remote server. The remote is mounted via SSH FS as this works nicely with the SSH agent running and uses the SSH config. The `pysftp` package is based on the Paramiko library that [doesn't support CA entries in the _known hosts_ file](https://github.com/paramiko/paramiko/issues/771) and therefore isn't of much use for me in the intended context.

In order to use this program, create a configuration file in TOML format somewhere. It must contain the following four elements:

```toml
remote = 'host:/path/to/your/workspace'
mountpoint = '/home/mu/mnt'
basedir = '/home/mu/your/workspace'
include = 'some/path/inside/basedir'
```

The _remote_ is what SSH FS shall mount. The _mountpoint_ is where it should mount that to. The _basedir_ is your local path that corresponds to what is mounted into the root of the _mountpoint_. Within that workspace you don't need to sync everything, you can also restrict it to some subdirectory via _include_. At the moment only one such include is supported.
