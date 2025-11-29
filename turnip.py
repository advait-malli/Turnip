#!/usr/bin/env python3

import io
import json
import os
import platform
import shutil
import zipfile
from pathlib import Path

import requests
from colorama import Fore, Style, init
from github import Github
from github.GithubException import UnknownObjectException

init(autoreset=True)


class Colors:
    MAGENTA = Fore.LIGHTMAGENTA_EX
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    GRAY = Fore.LIGHTBLACK_EX
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT


def print_banner():
    banner = f"""
{Colors.MAGENTA}╭───────────────────────────────────────╮
│                                       │
│               {Colors.BOLD}Turnip{Colors.RESET}{Colors.MAGENTA}                  │
│         GitHub Sync Manager           │
│                                       │
╰───────────────────────────────────────╯{Colors.RESET}
"""
    print(banner)


def print_status(message, status="info"):
    icons = {"success": "✓", "error": "✗", "warning": "⚠", "info": "→"}
    colors = {
        "success": Colors.GREEN,
        "error": Colors.RED,
        "warning": Colors.YELLOW,
        "info": Colors.GRAY,
    }

    icon = icons.get(status, "→")
    color = colors.get(status, Colors.GRAY)

    print(
        f"{Colors.MAGENTA}Turnip {color}{icon}{Colors.RESET} {Colors.GRAY}{message}{Colors.RESET}"
    )


def print_box(title, content_lines):
    width = 45
    print(
        f"\n{Colors.MAGENTA}╭─ {Colors.CYAN}{title}{Colors.MAGENTA} {'─' * (width - len(title) - 4)}╮{Colors.RESET}"
    )
    for line in content_lines:
        padding = width - len(
            line.replace(Colors.GRAY, "")
            .replace(Colors.RESET, "")
            .replace(Colors.CYAN, "")
        )
        print(
            f"{Colors.MAGENTA}│{Colors.RESET} {line}{' ' * padding}{Colors.MAGENTA}│{Colors.RESET}"
        )
    print(f"{Colors.MAGENTA}╰{'─' * width}╯{Colors.RESET}\n")


def get_config_path():
    home = Path.home()
    if platform.system() == "Windows":
        config_dir = home / "turnip" / "config"
    else:
        config_dir = home / ".config" / "turnip"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "cred.json"


def get_download_folder():
    home = Path.home()
    if platform.system() == "Windows":
        download_dir = home / "turnip" / "sync"
    else:
        download_dir = home / ".local" / "share" / "turnip" / "sync"

    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


config_path = get_config_path()

try:
    with open(config_path, "r") as file:
        input_dict = json.load(file)
    for key, value in input_dict.items():
        globals()[key] = eval(value)
except FileNotFoundError:
    print_status("Credentials not found. Please run setup first.", "error")
    exit(1)

g = Github(GITHUB_TOKEN)

print_banner()

REPO_NAME = input(f"{Colors.CYAN}Repository: {Colors.GRAY}{USERNAME}/{Colors.RESET}")
REPO_ADD = f"{USERNAME}/{REPO_NAME}"

try:
    repo = g.get_repo(REPO_ADD)
    print_status(f"Connected to {REPO_ADD}", "success")
except Exception as e:
    print_status(f"Failed to access repository: {e}", "error")
    exit(1)

DOWNLOAD_FOLDER = get_download_folder()

zip_url = f"https://github.com/{USERNAME}/{REPO_NAME}/archive/refs/heads/main.zip"
response = requests.get(zip_url)

if response.status_code == 200:
    shutil.rmtree(DOWNLOAD_FOLDER, ignore_errors=True)
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(DOWNLOAD_FOLDER)

    print_status(f"Downloaded to {DOWNLOAD_FOLDER}", "success")
    folder = DOWNLOAD_FOLDER / f"{REPO_NAME}-main"
    folder.rename(DOWNLOAD_FOLDER / REPO_NAME)
else:
    print_status(f"Download failed (Status: {response.status_code})", "error")
    exit(1)

print()
print_box(
    "Session Started",
    [
        f"{Colors.GRAY}Repository: {Colors.CYAN}{REPO_ADD}{Colors.RESET}",
        f"{Colors.GRAY}Location:   {Colors.CYAN}{DOWNLOAD_FOLDER / REPO_NAME}{Colors.RESET}",
    ],
)

print(f"{Colors.GRAY}Available commands:{Colors.RESET}")
print(
    f"  {Colors.CYAN}sync{Colors.RESET}           {Colors.GRAY}→ Sync changes to GitHub{Colors.RESET}"
)
print(
    f"  {Colors.CYAN}close{Colors.RESET}          {Colors.GRAY}→ Sync and close session{Colors.RESET}"
)
print(
    f"  {Colors.CYAN}close -dontsync{Colors.RESET} {Colors.GRAY}→ Close without syncing{Colors.RESET}"
)
print(
    f"  {Colors.CYAN}$<command>{Colors.RESET}     {Colors.GRAY}→ Run shell command in repo{Colors.RESET}"
)
print()


def delete_github_folder(repo, path):
    contents = repo.get_contents(path)
    for content in contents:
        if content.type == "dir":
            delete_github_folder(repo, content.path)
        else:
            try:
                repo.delete_file(content.path, f"Delete {content.path}", content.sha)
                print_status(f"Deleted {content.path}", "info")
            except Exception as e:
                print_status(f"Error deleting {content.path}: {e}", "error")


def upload_files_to_github(local_folder, repo):
    local_files = set()
    local_folder = Path(local_folder)

    print_status("Starting sync...", "info")

    for file_path in local_folder.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(local_folder)
            github_path = relative_path.as_posix()
            local_files.add(github_path)

            try:
                with open(file_path, "rb") as file_content:
                    try:
                        contents = repo.get_contents(github_path)
                        repo.update_file(
                            contents.path,
                            f"Update {github_path}",
                            file_content.read(),
                            contents.sha,
                        )
                    except UnknownObjectException:
                        try:
                            repo.create_file(
                                github_path,
                                f"Create {github_path}",
                                file_content.read(),
                            )
                        except UnknownObjectException:
                            pass
                    except Exception as e:
                        print_status(f"Error with {github_path}: {e}", "error")
            except FileNotFoundError:
                print_status(f"File not found: {file_path}", "warning")

    remote_files = repo.get_contents("")
    for content in remote_files:
        if content.path not in local_files:
            if content.type == "dir":
                delete_github_folder(repo, content.path)
            else:
                try:
                    repo.delete_file(
                        content.path, f"Delete {content.path}", content.sha
                    )
                    print_status(f"Deleted {content.path} (not in local)", "info")
                except Exception as e:
                    print_status(f"Error deleting {content.path}: {e}", "error")

    print_status("Sync complete", "success")


while True:
    cmd = input(
        f"{Colors.GRAY}{REPO_ADD}{Colors.RESET} {Colors.MAGENTA}│{Colors.RESET} {Colors.CYAN}>{Colors.RESET} "
    )

    upload_folder = DOWNLOAD_FOLDER / REPO_NAME

    if cmd == "close":
        print()
        upload_files_to_github(upload_folder, repo)
        shutil.rmtree(upload_folder, ignore_errors=True)
        print()
        print_status("Session closed", "success")
        print()
        break
    elif cmd == "sync":
        print()
        upload_files_to_github(upload_folder, repo)
        print()
    elif cmd == "close -dontsync":
        shutil.rmtree(upload_folder, ignore_errors=True)
        print()
        print_status("Session closed without syncing", "warning")
        print()
        break
    elif cmd == "help":
        print(f"{Colors.GRAY}Available commands:{Colors.RESET}")
        print(
            f"  {Colors.CYAN}sync{Colors.RESET}           {Colors.GRAY}→ Sync changes to GitHub{Colors.RESET}"
        )
        print(
            f"  {Colors.CYAN}close{Colors.RESET}          {Colors.GRAY}→ Sync and close session{Colors.RESET}"
        )
        print(
            f"  {Colors.CYAN}close -dontsync{Colors.RESET} {Colors.GRAY}→ Close without syncing{Colors.RESET}"
        )
        print(
            f"  {Colors.CYAN}<command>{Colors.RESET}     {Colors.GRAY}→ Run shell command in repo{Colors.RESET}"
        )
        print()
    elif cmd.strip() == "":
        continue
    else:
        os.chdir(upload_folder)
        os.system(cmd)

