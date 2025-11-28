from github import Github
import os, requests, zipfile, io, shutil, json, platform
from pathlib import Path
from github.GithubException import UnknownObjectException
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Determine the appropriate config path based on OS
def get_config_path():
    home = Path.home()
    if platform.system() == "Windows":
        config_dir = home / "turnip" / "config"
    else:  # macOS and Linux
        config_dir = home / ".config" / "turnip"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "cred.json"

# Load credentials
config_path = get_config_path()
with open(config_path, 'r') as file:
    input_dict = json.load(file)
for key, value in input_dict.items():
    globals()[key] = eval(value)
    
# GitHub setup
g = Github(GITHUB_TOKEN)

REPO_NAME = input(Fore.LIGHTMAGENTA_EX + f"\nGithub Repo: " + Fore.LIGHTBLACK_EX + f"{USERNAME}/" + Style.RESET_ALL)
REPO_ADD = f"{USERNAME}/{REPO_NAME}"
repo = g.get_repo(REPO_ADD)

# Determine the appropriate download folder based on OS
def get_download_folder():
    home = Path.home()
    if platform.system() == "Windows":
        download_dir = home / "turnip" / "sync"
    else:  # macOS and Linux
        download_dir = home / ".local" / "share" / "turnip" / "sync"
    
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir

DOWNLOAD_FOLDER = get_download_folder()

# Download and extract the repository
zip_url = f"https://github.com/{USERNAME}/{REPO_NAME}/archive/refs/heads/main.zip"
response = requests.get(zip_url)

if response.status_code == 200:
    shutil.rmtree(DOWNLOAD_FOLDER, ignore_errors=True)
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(DOWNLOAD_FOLDER)

    print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Repository '{REPO_ADD}' downloaded and extracted to {DOWNLOAD_FOLDER}." + Style.RESET_ALL)
    folder = DOWNLOAD_FOLDER / f"{REPO_NAME}-main"
    folder.rename(DOWNLOAD_FOLDER / REPO_NAME)
else:
    print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Failed to download repository. Status code: {response.status_code}" + Style.RESET_ALL)

print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Session started on repository: '{REPO_ADD}'\n" + Style.RESET_ALL)

def delete_github_folder(repo, path):
    """Delete a folder and its contents on GitHub."""
    contents = repo.get_contents(path)
    for content in contents:
        if content.type == "dir":
            delete_github_folder(repo, content.path)
        else:
            try:
                repo.delete_file(content.path, f"Delete {content.path}", content.sha)
                print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Deleted file '{content.path}' from GitHub." + Style.RESET_ALL)
            except Exception as e:
                print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Error deleting file '{content.path}': {e}" + Style.RESET_ALL)

    try:
        repo.delete_file(path, f"Delete folder {path}", contents[0].sha)
        print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Deleted folder '{path}' from GitHub." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Error deleting folder '{path}': {e}" + Style.RESET_ALL)

def upload_files_to_github(local_folder, repo):
    """Upload or update files to GitHub."""
    local_files = set()
    local_folder = Path(local_folder)

    for file_path in local_folder.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(local_folder)
            github_path = relative_path.as_posix()  # Convert to forward slashes for GitHub
            local_files.add(github_path)

            try:
                with open(file_path, 'rb') as file_content:
                    try:
                        contents = repo.get_contents(github_path)
                        repo.update_file(contents.path, f"Update {github_path}", file_content.read(), contents.sha)
                    except UnknownObjectException:
                        try:
                            repo.create_file(github_path, f"Create {github_path}", file_content.read())
                        except UnknownObjectException:
                            pass
                    except Exception as e:
                        print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Error with '{github_path}': {e}" + Style.RESET_ALL)
            except FileNotFoundError:
                print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" File not found: {file_path}" + Style.RESET_ALL)

    remote_files = repo.get_contents("")
    for content in remote_files:
        if content.path not in local_files:
            if content.type == "dir":
                delete_github_folder(repo, content.path)
            else:
                try:
                    repo.delete_file(content.path, f"Delete {content.path}", content.sha)
                    print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Deleted '{content.path}' from GitHub as it no longer exists locally.")
                except Exception as e:
                    print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + f" Error deleting '{content.path}': {e}")

    print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + " Synced to Repo\n" + Style.RESET_ALL)


while True:
    cmd = input(Fore.LIGHTBLACK_EX + f"{REPO_ADD}"+ Style.RESET_ALL + Fore.LIGHTMAGENTA_EX + " | Turnip> " + Style.RESET_ALL)
    
    upload_folder = DOWNLOAD_FOLDER / REPO_NAME
    
    if cmd == "close":
        upload_files_to_github(upload_folder, repo)
        shutil.rmtree(upload_folder, ignore_errors=True)
        print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + " Session closed\n" + Style.RESET_ALL)
        break
    elif cmd == "sync":
        upload_files_to_github(upload_folder, repo)
    elif cmd == "close -dontsync":
        shutil.rmtree(upload_folder, ignore_errors=True)
        print(Fore.LIGHTMAGENTA_EX + f"\nTurnip:~" + Fore.LIGHTBLACK_EX + " Session closed without syncing to repo\n" + Style.RESET_ALL)
        break
    elif cmd.startswith("$"):
        os.chdir(upload_folder)
        os.system(cmd[1:])
