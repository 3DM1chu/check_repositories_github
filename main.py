import jsonpickle
import sys
import requests
import os
from bs4 import BeautifulSoup


class Commit:
    def __init__(self):
        self.commit_date = ""
        self.commit_title = ""
        self.commit_id = ""

    def parse(self, data):
        self.commit_date = data.findNext('h2', attrs={'class': 'f5 text-normal'}).contents[0].split("Commits on ")[1]
        self.commit_id = data.findNext('a', attrs={'class': 'markdown-title'})['href'].split("/")[-1]
        self.commit_title = data.findNext('a', attrs={'class': 'markdown-title'}).contents[0][:-2].replace("\n", "")


class GithubProjectHistory:
    def __init__(self, link = ""):
        self.commits = []
        self.new_commits = []
        self.link : str = link
        if link != "":
            if self.link[-1] != "/":
                self.link += "/"
            self.repo_name : str = self.link.split("/")[-2]
            self.author_name : str = self.link.split("/")[-3]
        else:
            self.repo_name : str = ""
            self.author_name : str = "Unknown"
        self.file_url : str = "projects_watched/" + self.repo_name + " _ " + self.author_name + ".json"

    def loadFromFile(self, file_url):
        file = open(file_url, "r")
        self.file_url = file_url
        git : GithubProjectHistory = jsonpickle.decode(file.read())
        file.close()
        self.link = git.link
        self.author_name = git.author_name
        self.repo_name = git.repo_name
        self.file_url = git.file_url
        self.commits = git.commits
        self.new_commits = []
        return self

    def checkAndAddCommit(self, commit: Commit):
        for commit_in_db in self.commits:
            if commit_in_db.commit_id == commit.commit_id:
                return False
        self.commits.append(commit)
        return True

    def parseCommitsFromServer(self):
        resp = requests.get(self.link + "/commits/master")
        soup = BeautifulSoup(resp.content, 'html.parser')
        commits_parsed = soup.findAll('div', attrs={'class': 'TimelineItem'})
        self.new_commits.clear()
        for timeline in commits_parsed:
            commit = Commit()
            commit.parse(timeline)
            if self.checkAndAddCommit(commit):
                print(f"PARSED NEW COMMIT | from {commit.commit_date} : {commit.commit_title}")
                self.new_commits.append(commit)
        file_to_save = open(self.file_url, "w+")
        file_to_save.write(jsonpickle.encode(self, indent=2))
        file_to_save.close()


class UpdateManager:
    def __init__(self):
        self.projects = [] # github project objects

    def watchProject(self, project: GithubProjectHistory):
        self.projects.append(project)

    def checkAllProjectsAndSendEmail(self):
        updates = []
        for project in self.projects:
            project.parseCommitsFromServer()
            if len(project.new_commits) > 0:
                updates.append(project)
        return updates


class Configuration:
    def __init__(self):
        self.SMTP_API_KEY = ""

    def read_api_key(self):
        f = open("api_key.txt", "a+")
        self.SMTP_API_KEY = str(f.readline())
        f.close()

    def read_github_projects(self, updater):
        github_projects = os.listdir("projects_watched")
        for github_project_file in github_projects:
            project = GithubProjectHistory().loadFromFile("projects_watched/" + github_project_file)
            updater.watchProject(project)
        print(f"{len(github_projects)} GitHub project/s in projects_watched loaded")


if __name__ == "__main__":  # Makes sure this is the main process
    args = sys.argv
    #github_to_check = args[1]
    config = Configuration()
    config.read_api_key()
    print(config.SMTP_API_KEY)

    #updater = UpdateManager()
    #config.read_github_projects(updater)
    #updater.checkAllProjectsAndSendEmail()

    github_project = GithubProjectHistory(link="https://github.com/imartinez/privateGPT")
    github_project.parseCommitsFromServer()
