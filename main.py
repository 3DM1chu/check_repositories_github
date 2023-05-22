import jsonpickle
import sys
import requests
from bs4 import BeautifulSoup


class Commit:
    def __init__(self):
        self.commit_date = ""
        self.commit_title = ""
        self.commit_id_link = ""

    def parse(self, data):
        self.commit_date = data.findNext('h2', attrs={'class': 'f5 text-normal'}).contents[0].split("Commits on ")[1]
        self.commit_id_link = data.findNext('a', attrs={'class': 'markdown-title'})['href']
        self.commit_title = data.findNext('a', attrs={'class': 'markdown-title'}).contents[0][:-2].replace("\n", "")


class GithubProjectHistory:
    def __init__(self, link = ""):
        self.commits = []
        self.link : str = link
        if link != "":
            self.repo_name : str = self.link.split("/")[-2]
            self.author_name : str = self.link.split("/")[-3]
        else:
            self.repo_name : str = ""
            self.author_name : str = "Unknown"
        self.file_url : str = "projects_watched/" + self.repo_name + ".txt"

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
        return self

    def checkAndAddCommit(self, commit: Commit):
        for commit_in_db in self.commits:
            if commit_in_db.commit_id_link == commit.commit_id_link:
                return False
        self.commits.append(commit)
        return True

    def parseCommitsFromServer(self):
        resp = requests.get(self.link + "/commits/master")
        soup = BeautifulSoup(resp.content, 'html.parser')
        commits_parsed = soup.findAll('div', attrs={'class': 'TimelineItem'})
        for timeline in commits_parsed:
            commit = Commit()
            commit.parse(timeline)
            if self.checkAndAddCommit(commit):
                print("PARSED NEW COMMIT: " + commit.commit_title)
        file_to_save = open(self.file_url, "w+")
        file_to_save.write(jsonpickle.encode(self, indent=2))
        file_to_save.close()


class Configuration:
    def __init__(self):
        self.SMTP_API_KEY = ""

    def read_api_key(self):
        f = open("api_key.txt", "a+")
        self.SMTP_API_KEY = str(f.readline())
        f.close()


if __name__ == "__main__":  # Makes sure this is the main process
    args = sys.argv
    #github_to_check = args[1]
    config = Configuration()
    config.read_api_key()
    print(config.SMTP_API_KEY)

    github_project = GithubProjectHistory().loadFromFile("projects_watched/Auto-GPT.txt")
    github_project = GithubProjectHistory(link="https://github.com/Significant-Gravitas/Auto-GPT/")
    github_project.parseCommitsFromServer()
