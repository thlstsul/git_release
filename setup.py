from setuptools import setup

setup(
    name="git-release",
    version="0.1.0",
    description="Git项目自动发布工具 - 自动更新版本号、提交、打标签、推送",
    author="thlstsul",
    author_email="zhouzm5@qq.com",
    py_modules=["git_release"],
    entry_points={
        "console_scripts": [
            "git-release=git_release:main",
        ],
    },
    install_requires=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.6",
)
