import sol


class SSCS:
    CATEGORIES = (
        "TODO",
        "TODO?",
        "IDEA",
        "FIXME"
    )

    def __init__(self):
        pass

    def taskdict_from_project(self):
        pass
        # for file in project:
        #   for line in file:
        #       for category in categories:
        #           if category in line:
        #               self.taskdict.append(
        #                   filename,
        #                   CodeTask.from_comment_string(line)
        #               )

    def main(self):
        print("Running Sol Source Code Scraper.")


def main():
    SSCS().main()
