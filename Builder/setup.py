from setuptools import setup, find_packages
import sys, platform

python_version = platform.python_version()
packageversion = str(sys.argv[-1])

if platform.system() == "Darwin":
    platform_machine = "macosx_"+"_".join(platform.mac_ver()[0].split("."))+"_"+platform.machine()
else:
    platform_machine = platform.system()+"-"+platform.machine()

def removeArgs():
    if packageversion in sys.argv:
        sys.argv.remove(packageversion)


removeArgs()


setup(
    name="gustavo",
    version=str(packageversion),
    author="Paritosh Ramanan",
    author_email="paritosh.ramanan@okstate.edu",
    description="Project Gustavo: Manage container images across distributed edge resources",
    packages=find_packages(),
    package_data={
        "gustavo": [
            "images/*",
            "src/*",
            "src/__pycache__/*",
            "gui/*",
            "gui/__pycache__/*",
            "sample_config_files/*",
        ]
    },options={
        "bdist_wheel": {
            "plat_name": platform_machine,
            "python_tag": "py{}{}".format(sys.version_info[0],sys.version_info[1]),
        }
    },
    classifiers=[
        "Programming Language :: Python :: {}".format(python_version),
        "Operating System :: Linux"
    ],
    install_requires=[
        "NebulaPythonSDK==2.8.0",
        "python-dotenv==0.19.0",
        "pyYAML==6.0",
        "Click==8.1.3",
        "urllib3==1.26.12",
        "requests==2.28.1",
        "six==1.16.0",
        "Flask==2.2.2",
        "redis==4.3.4",
        "gunicorn==20.1.0",
        "retrying==1.3.3",
        "docker==6.0.0",
        "python-on-whales==0.70.0",
        "streamlit==1.37.0",
        "streamlit-card==1.0.0",
        "streamlit-pills==0.3.0",
        "plotly==5.20.0"
    ],
    python_requires=">={}".format(python_version),
    entry_points="""
        [console_scripts]
        gustavo=gustavo.gustavo:gustavo
    """,
)
