import sys
import os
import subprocess
from pathlib import Path
import re

"""

To build python library package e.g python builder.py repo_url

"""

gitRepo = str(sys.argv[1])
if len(sys.argv)>2:
    mode = "prod"
    GEMFURY_TOKEN = str(sys.argv[2])
else:
    mode = "dev"
    GEMFURY_TOKEN = ""

if gitRepo:

    currentDir = os.getcwd()

    subprocess.run(["git", "remote", "update"])

    versionInfo = str(os.popen("git describe --tags").read())
    versionInfo = re.search(r'([\d.]+)', versionInfo).group(1)

    print(
        "\033[1m"
        + "\n\n\n\t\t\t__________________Creating Output directory __________________\n"
        + "\033[0m"
    )
    os.system("mkdir temp")
    tempDir = currentDir + "/temp"
    os.chdir(Path(tempDir))
    print(
        "\033[1m"
        + "\n\n\n\t\t\t__________________Cloning Git Repo __________________\n"
        + "\033[0m"
    )
    subprocess.run(["git", "clone", "-b", "main", gitRepo])

    os.chdir(Path(str(currentDir + "/temp/gustavo")))
    os.chdir(Path(currentDir + "/temp"))
    os.system("touch __init__.py")
    print(
        "\033[1m"
        + "\n\n\n\t\t\t__________________ Creating Sym link for setup, README files __________________\n"
        + "\033[0m"
    )
    os.system("ln -sf {}/setup.py {}".format(currentDir, tempDir))
    os.system("ln -sf {}/README.md {}".format(currentDir, tempDir))
    os.system("ln -sf {}/dev_reinstall.sh {}".format(currentDir, tempDir))


    print("Version: {}".format(versionInfo))

    buildWheelPkg = "python setup.py bdist_wheel" + " " + str(versionInfo)

    os.system(buildWheelPkg)

    distpath = str(currentDir) + "/temp/dist/"

    os.chdir(Path(distpath))

    packageInfo = os.listdir(distpath)[0]

    if mode == "prod":
        subprocess.run(
            [
                "curl",
                "-F",
                "package=@" + str(packageInfo),
                "https://{}@push.fury.io/osu-home-stri/".format(GEMFURY_TOKEN),
            ]
        )

        os.chdir(currentDir)

        os.system("yes | rm -r temp")


else:
    print("provide Git repo details")
