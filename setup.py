from setuptools import setup, find_packages

setup(
    name="citadel",
    version="0.0.0",
    packages=find_packages(exclude=["tests*"]),
    install_requires=["colorama"],
    extras_require={
        "dev": ["pytest", "pytest-mock", "pytest-asyncio", "pytest-cov"]
    }
)
