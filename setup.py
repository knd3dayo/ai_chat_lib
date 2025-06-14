from setuptools import setup, find_packages

def get_requirements_from_file():
    with open("requirements.txt") as f:
        return f.read().splitlines()

setup(
    name="ai_chat_lib",
    version="0.1.0",
    author="knd3dayo",
    author_email="knd3dayo@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements_from_file(),
)