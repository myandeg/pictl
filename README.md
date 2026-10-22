# pictl

A command line tool for Image Compression and Upload (ex. S3-type)

> **This is a personal fork** of [zhonger/pictl](https://github.com/zhonger/pictl), used locally only
> (installed with `pipx install -e`, not published to PyPI or Homebrew). See
> [Fork notes](#fork-notes-v040) below for what's different and why.

Engligh | [中文简体](https://lisz.me/tech/project/pictl.html)

## Why a new project

When I publish blog articles, it's quite inefficient for me to prepare images.

Although there exist many good enough tools, like [uPic](https://github.com/gee1k/uPic), [PicGo](https://github.com/Molunerfinn/PicGo), and so on, they still cannot meet my need completely.

For me, these points are very necessary:

- All images should be compressed and transformed into `webp` format (less storage and loading time).
- All images can be uploaded to S3-like object storage with a unique short name.
- It should be very easy to use. It‘s better if no web UI or GUI. Command line first.
- (Optional) The customized watermark can be added into all images automatically.
- (Optional) All images can be resized into the defined default size automatically.
- (Optional) It defaults to read the image from the clipboard.

Actually uPic and PicGo can provide most of the above functions, but not so good in some points.

- They don't provide the transformation to `webp` format.
- They don't provide the support for Cloudflare R2 (though uPic paid version in appstore provides it).

It's quite time-consuming for me to write a plugin for PicGo or rewrite codes for uPic.

So why not write a new tool?

## The project name

Because it's designed for image helper in writing blog articles and using only with command line,
it's named PICTL, a short name for **Pi**cture **C**on**t**ro**l**.

## The architecture

Here is the architecture of this project.

It seems very similar to PicGo 😂, but it will be different.

![The architecture](https://github.com/zhonger/pictl/assets/12064158/4560bc88-c58e-4f35-8dd3-0ccc4ff36673)

## Installation

### This fork (pipx, editable)

The way this fork is actually installed and kept up to date locally:

```bash
brew install pipx
pipx ensurepath
git clone git@github.com:myandeg/pictl.git ~/Developer/pictl
pipx install -e ~/Developer/pictl
```

Editable install means edits under `~/Developer/pictl` take effect immediately — no reinstall needed.

If your system's default Python has no prebuilt `Pillow` wheel yet (very new Python version), pin pipx
to an older interpreter that does, e.g.:

```bash
pipx install -e ~/Developer/pictl --python "$(brew --prefix python@3.11)/bin/python3.11"
```

### PIP (upstream package, not this fork)

```bash
pip3 install pictl
```

This installs **upstream's** released package from PyPI, which does not include this fork's changes.
Upstream also pins `Pillow = "^9.3.0"` (i.e. `<10.0.0`), which has no prebuilt wheel for recent Python
versions and fails to build from source — this fork relaxes that pin (see below).

### Brew — currently broken, don't use

```bash
brew tap zhonger/pictl
brew install pictl
```

As of this fork, `brew install pictl` fails: the formula depends on the `six` Homebrew package, which
no longer exists in homebrew-core. Use the pipx method above instead.

## Usage

### Config

The config file for PICTL is named `.pictlrc` with `toml` format. The config file is located at `~/.pictlrc`.

Until now PICTL supports:

| Name | `type` in config |
| :--: | :--: |
| Cloudflare R2 | `R2` |
| AWS S3 | `S3` |
| Tencent COS | `COS(Tencent)` |

#### Manually

```bash
[basic]
length = 6
ntype = "random"
algorithm = "sha1"
optimize = true   # passed to Pillow's webp encoder
quality = 80      # passed to Pillow's webp encoder (default 75)

[blog]
type = "S3"
endpoint = "https://s3.ap-northeast-1.amazonaws.com"
bucket = "blog"
region = "ap-northeast-1"
prefix = "blog"
key = "this-is-a-long-key-for-s3"
secret = "this-is-a-long-secret-for-s3"
url = "https://i.lisz.me"
```

Cloudflare R2 example (the `endpoint` is account-level, `region` is always `"auto"`):

```bash
[notes]
type = "R2"
endpoint = "https://<ACCOUNT_ID>.r2.cloudflarestorage.com"
bucket = "notes-img"
region = "auto"
prefix = "Img"
key = "<R2_ACCESS_KEY_ID>"
secret = "<R2_SECRET_ACCESS_KEY>"
url = "https://img.example.com"
```

R2 does not implement S3 object ACLs (`x-amz-acl`) — if a client sends anything other than `private`,
R2 returns `501 NotImplemented`. Public read access has to be set at the bucket level in the Cloudflare
dashboard (custom domain or `r2.dev` subdomain), not via an ACL header.

### Interactive way

```bash
╰─$ pictl config
Usage: pictl config [OPTIONS] COMMAND [ARGS]...

  Operations for the config file `~/.pictlrc`.

Options:
  -h, --help  Show this message and exit.

Commands:
  add     Add configs to the config file.
  delete  Delete config group from the config file.
  info    Check the configs.
  init    Initialize config file with default configs
```

### Compress + upload (`cup`)

```
Usage: pictl cup [OPTIONS] FILENAMES...

  Compress image(s) and upload to remote storage.

Options:
  -g, --group TEXT  The group in the config file you want to use.  [required]
  -q, --quiet        Only print the resulting URL(s), one per line, in input
                      order.
  -h, --help          Show this message and exit.
```

`GROUP` is an option (`-g`/`--group`), not a trailing positional argument, specifically so that
`FILENAMES` can be the *last* thing on the command line — that's what lets a tool like Typora, which
appends the file path(s) it's uploading to the end of whatever command you configured, work correctly:

```bash
pictl cup -g notes -q /path/to/image1.png /path/to/image2.png
```

With `-q/--quiet`, stdout is exactly one URL per line (nothing else) and the process exits non-zero if
any file failed — diagnostics for failures go to stderr instead, so stdout stays clean. Without `-q`,
each upload prints the direct URL, a ready-made Markdown snippet, and an HTML `<img>` tag.

Compressed `.webp` output is written to the system temp directory and deleted after a successful (or
failed) upload attempt — not to the current working directory. This matters because apps that shell out
to external uploaders (Typora included) often run the child process with a working directory that's
read-only (e.g. on macOS's sealed system volume), so writing a bare relative filename fails with
`OSError: [Errno 30] Read-only file system`.

Images with an alpha channel (e.g. transparent PNGs/screenshots) keep their transparency in the output
webp — upstream unconditionally converted everything to RGB first, which silently flattened transparent
pixels to black/white.

#### Typora integration

Typora → Preferences → Image → Image Uploader → `Custom Command`, and set the command to:

```
/path/to/pictl cup -g notes -q
```

Use `pictl`'s absolute path (`which pictl`), since the environment a GUI app launches a process in may
not have your shell's `PATH`.

## Fork notes (v0.4.0)

Changes on top of upstream [v0.3.0](https://github.com/zhonger/pictl/releases/tag/v0.3.0), kept here
for my own future reference:

- **Pillow version unpinned** (`^9.3.0` → `>=10.0.0`). Upstream's exact caret range resolves to an old
  Pillow with no wheel for current Python, so `pip`/`pipx install` fails trying to build it from source.
- **Alpha channel preserved** in webp output instead of always flattening to RGB.
- **`cup`/`upload` accept multiple files** (`nargs=-1`) and a `-q/--quiet` flag that prints one bare URL
  per line and exits non-zero on any failure, with diagnostics on stderr. Needed because upstream's
  three-line human-readable output (`Direct URL:` / `Markdown:` / `HTML Code:`) isn't something a tool
  like Typora can parse directly.
- **`GROUP` is `-g/--group`, not a positional argument** — so `FILENAMES` can be last, matching how
  Typora's custom-command uploader appends file paths to the end of the configured command.
- **Compressed output goes to the system temp dir, not the CWD**, and is deleted after upload. Fixes a
  crash when the caller's working directory is read-only (seen with Typora on macOS).
- Not published anywhere — installed locally with `pipx install -e`.
