import argparse
import requests
import json
import os
import base64
import shutil
import stat

with open(".access_key", "r") as f:
    key = f.read()

headers = {"Accept": "application/vnd.github+json",
           "Authorization": "token {}".format(key),
           "X-GitHub-Api-Version": "2022-11-28"}

def create_dir(path, clean=False):
    if not os.path.isdir(path):
        os.makedirs(path)
    elif clean:
        os.remove(os.path.join(path, "*"))

def get_user_info(username, save=False, update=False):
    answer = requests.get("https://api.github.com/users/{}".format(username), headers=headers)
    content = json.loads(answer.content.decode(encoding="utf-8"))

    if save:
        if update or not os.path.isfile(os.path.join("github_data", "user.json")):
            create_dir("github_data")
            with open(os.path.join("github_data", "user.json"), "w") as f:
                f.write(json.dumps(content))

    return content

def get_repos_info(user_info, save=False, update=False):
    answer = requests.get(user_info["repos_url"], headers=headers)
    # print(answer)
    content = json.loads(answer.content.decode(encoding="utf-8"))

    if save:
        if update or not os.path.isfile(os.path.join("github_data", "repos.json")):
            create_dir("github_data")
            with open(os.path.join("github_data", "repos.json"), "w") as f:
                f.write(json.dumps(content))

    return content

def get_repo_info(repos_info, repo_name, save=False, update=False):
    for repo in repos_info:
        if repo_name == repo["name"]:
            answer = requests.get(repo["url"], headers=headers)
            content = json.loads(answer.content.decode(encoding="utf-8"))

            if save:
                if update or not os.path.isfile(os.path.join("github_data", "{}.json".format(repo_name))):
                    create_dir("github_data")
                    with open(os.path.join("github_data", "{}.json".format(repo_name)), "w") as f:
                        f.write(json.dumps(content))
            
            return content

def get_repo_readme_content(repo_info, save=False, update=False):
    answer = requests.get(repo_info["url"]+"/readme", headers=headers)
    # answer = requests.get("https://api.github.com/repos/JeanLeBris/argparse_cpp/readme")
    # content = json.loads(answer.content.decode(encoding="utf-8"))
    content = base64.b64decode(json.loads(answer.content.decode(encoding="utf-8"))["content"]).decode(encoding="utf-8")
    print(content)

    # if save:
    #     if update or not os.path.isfile(os.path.join("github_data", "repos.json")):
    #         create_dir("github_data")
    #         with open(os.path.join("github_data", "repos.json"), "w") as f:
    #             f.write(json.dumps(content))

    return content

def get_repo_files(repo_info, file_name, save=False, update=False):
    answer = requests.get(repo_info["url"]+"/contents/{}".format(file_name), headers=headers)
    # answer = requests.get("https://api.github.com/repos/JeanLeBris/argparse_cpp/readme")
    content = json.loads(answer.content.decode(encoding="utf-8"))
    # content = base64.b64decode(json.loads(answer.content.decode(encoding="utf-8"))["content"]).decode(encoding="utf-8")
    # print(content)

    if save:
        if update or not os.path.isfile(os.path.join("github_data", "files.json")):
            create_dir("github_data")
            with open(os.path.join("github_data", "files.json"), "w") as f:
                f.write(json.dumps(content))

    return content

def get_repo_file_tree(repo_info, file_name, save=False, update=False):
    output = list()
    if file_name == "":
        output.append(None)
    
    output += get_repo_files(repo_info, file_name, save, update)

    for i in range(len(output)):
        if output[i] != None:
            if output[i]["type"] == "dir":
                buffer = output[i]
                output[i] = list()
                output[i].append(buffer)
                output[i] += get_repo_file_tree(repo_info, output[i][0]["path"], save, update)
    
    if save:
        if update or not os.path.isfile(os.path.join("github_data", "files.json")):
            create_dir("github_data")
            with open(os.path.join("github_data", "files.json"), "w") as f:
                f.write(json.dumps(output))

    return output

def print_repo_file_tree(repo_file_tree, level=0, save=False, update=False):
    for i in range(len(repo_file_tree)):
        if repo_file_tree[i] != None:
            if isinstance(repo_file_tree[i], list):
                print_repo_file_tree(repo_file_tree[i], level+1, save, update)
            else:
                name = repo_file_tree[i]["name"]
                if repo_file_tree[i]["type"] == "file":
                    for i in range(level):
                        print("    ", end="")
                    print(name)
                elif repo_file_tree[i]["type"] == "dir":
                    for i in range(level-1):
                        print("    ", end="")
                    print(name)

def get_repo_file_content(repo_info, file_name, save=False, update=False):
    answer = requests.get(repo_info["url"]+"/contents/{}".format(file_name), headers=headers)
    # answer = requests.get("https://api.github.com/repos/JeanLeBris/argparse_cpp/readme")
    # content = json.loads(answer.content.decode(encoding="utf-8"))
    content = base64.b64decode(json.loads(answer.content.decode(encoding="utf-8"))["content"]).decode(encoding="utf-8")
    print(content)

    # if save:
    #     if update or not os.path.isfile(os.path.join("github_data", "repos.json")):
    #         create_dir("github_data")
    #         with open(os.path.join("github_data", "repos.json"), "w") as f:
    #             f.write(json.dumps(content))

    return content

def clone_repo(repo_info, save=False, update=False):
    clone_url = repo_info["clone_url"]
    os.system("git clone {} {}".format(clone_url, os.path.join("..", repo_info["name"])))

def remove_repo(repo_info, save=False, update=False):
    for root, dirs, files in os.walk(os.path.join("..", repo_info["name"])):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IRWXU)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IRWXU)
    shutil.rmtree(os.path.join("..", repo_info["name"]))

def install_repo(repo_info, save=False, update=False):
    os.system("cd {} && make compile LIBRARY_TYPE=static OS=Windows_NT".format(os.path.join("..", repo_info["name"])))

def clean_repo(repo_info, save=False, update=False):
    os.system("cd {} && make clean LIBRARY_TYPE=static OS=Windows_NT".format(os.path.join("..", repo_info["name"])))

if __name__ == "__main__":
    username = "JeanLeBris"

    save = True
    update = False

    parser = argparse.ArgumentParser("installer", description="program to install Jean Le Bris' repositories")
    parser_1 = parser.add_subparsers(dest="request")
    parser_1.add_parser("user")
    parser_1.add_parser("repos")
    parser_1_3 = parser_1.add_parser("repo")
    parser_1_3.add_argument("repo", action="store", type=str, help="name of the repository")
    parser_1_4 = parser_1.add_parser("files")
    parser_1_4.add_argument("repo", action="store", type=str, help="name of the repository")
    parser_1_4 = parser_1.add_parser("file")
    parser_1_4.add_argument("repo", action="store", type=str, help="name of the repository")
    parser_1_4.add_argument("file", action="store", type=str, help="path of the file")
    parser_1_4 = parser_1.add_parser("clone")
    parser_1_4.add_argument("repo", action="store", type=str, help="name of the repository")
    parser_1_4 = parser_1.add_parser("remove")
    parser_1_4.add_argument("repo", action="store", type=str, help="name of the repository")
    parser_1_4 = parser_1.add_parser("install")
    parser_1_4.add_argument("repo", action="store", type=str, help="name of the repository")
    parser_1_4 = parser_1.add_parser("clean")
    parser_1_4.add_argument("repo", action="store", type=str, help="name of the repository")
    # parser_1.add_argument("request", action="store", type=str, help="type of request to do")
    args = parser.parse_args()
    # print(args)
    request = args.request

    if request == "user":
        user_info = get_user_info(username, save, update)
        # with open("answer.json", "w") as f:
        #     f.write(json.dumps(user_info))
        # for project in json.loads(answer.content):
        #     print(project['name'])
        print(user_info["login"])

    elif request == "repos":
        user_info = get_user_info(username, save, update)
        repos_info = get_repos_info(user_info, save, update)
        # with open("answer.json", "w") as f:
        #     f.write(json.dumps(repos_info))
        print("Jean Le bris' list of repositories :")
        print("Installed\tRepository")
        for project in repos_info:
            print(" [{}]\t{}".format("Y" if os.path.isdir(os.path.join("..", project['name'])) else "N", project['name']))
        # print(json.loads(answer.content))
    
    elif request == "repo":
        repo_name = args.repo
        user_info = get_user_info(username, save, update)
        repos_info = get_repos_info(user_info, save, update)
        repo_info = get_repo_info(repos_info, repo_name, save, update)
    
    elif request == "files":
        repo_name = args.repo
        user_info = get_user_info(username, save, update)
        repos_info = get_repos_info(user_info, save, update)
        repo_info = get_repo_info(repos_info, repo_name, save, update)
        repo_files = get_repo_file_tree(repo_info, "", save, update)
        # print(repo_files)
        print_repo_file_tree(repo_files, 0, save, update)

    elif request == "file":
        repo_name = args.repo
        file_path = args.file
        user_info = get_user_info(username, save, update)
        repos_info = get_repos_info(user_info, save, update)
        repo_info = get_repo_info(repos_info, repo_name, save, update)
        get_repo_file_content(repo_info, file_path)

    elif request == "clone":
        repo_name = args.repo
        user_info = get_user_info(username, save, update)
        repos_info = get_repos_info(user_info, save, update)
        repo_info = get_repo_info(repos_info, repo_name, save, update)
        # get_repo_readme_content(repo_info)
        # get_repo_file_content(repo_info, ".gitignore")
        clone_repo(repo_info, save, update)

    elif request == "remove":
        repo_name = args.repo
        user_info = get_user_info(username, save, update)
        repos_info = get_repos_info(user_info, save, update)
        repo_info = get_repo_info(repos_info, repo_name, save, update)
        # get_repo_readme_content(repo_info)
        # get_repo_file_content(repo_info, ".gitignore")
        remove_repo(repo_info, save, update)
    
    elif request == "install":
        repo_name = args.repo
        user_info = get_user_info(username, save, update)
        repos_info = get_repos_info(user_info, save, update)
        repo_info = get_repo_info(repos_info, repo_name, save, update)
        install_repo(repo_info, save, update)
    
    elif request == "clean":
        repo_name = args.repo
        user_info = get_user_info(username, save, update)
        repos_info = get_repos_info(user_info, save, update)
        repo_info = get_repo_info(repos_info, repo_name, save, update)
        clean_repo(repo_info, save, update)