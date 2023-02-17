from setuptools import setup, find_packages
import sys


packageversion = str(sys.argv[-1])


def removeArgs():
    if packageversion in sys.argv:
        sys.argv.remove(packageversion)


removeArgs()


setup(
    name="gustavo",
    version=str(packageversion),
    author="Paritosh Ramanan",
    author_email="paritosh.ramanan@okstate.edu",
    description="Project Gustavo: A CLI tool to manage container images across distributed edge resources",
    packages=find_packages(),
    package_data={
        "gustavo": [
            "dist/linux/gustavo",
            "src/*",
            "src/__pycache__/*",
            "sample_config_files/*",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "NebulaPythonSDK==2.8.0",
        "python-dotenv==0.21.0",
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
        "python-on-whales==0.52.0",
    ],
    python_requires=">=3.7",
    entry_points="""
        [console_scripts]
        gustavo=gustavo.gustavo:gustavo
    """,
)
