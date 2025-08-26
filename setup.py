from setuptools import setup, find_packages

setup(
    name="nsgtree",
    version="0.6.5",
    description="New SGTree: Build genome tree from concatenated alignment after hmmsearch using a set of user provided HMMs",
    author="Frederik Schulz, Juan C. Villada",
    author_email="fschulz@lbl.gov",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "biopython>=1.78",
        "pandas>=1.5",
        "numpy>=1.23",
        "scipy>=1.9",
        "pyyaml>=6.0",
        "ete3>=3.1",
        "typer>=0.9.0",
        "rich>=13.0.0",
    ],
    entry_points={
        'console_scripts': [
            'nsgtree=nsgtree.cli:app',
        ],
    },
    include_package_data=True,
    package_data={
        'nsgtree': ['config/*.yml', 'resources/models/*.hmm'],
    },
)
