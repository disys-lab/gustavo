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

    print("Version: {}".format(versionInfo))

    buildWheelPkg = "python setup.py bdist_wheel" + " " + str(versionInfo)

    os.system(buildWheelPkg)

    distpath = "./dist/"

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
