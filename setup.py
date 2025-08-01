from setuptools import setup, find_packages

setup(
    name="nsgtree",
    version="0.5.0",
    description="New SGTree: Build genome tree from concatenated alignment after hmmsearch using a set of user provided HMMs",
    author="Frederik Schulz",
    author_email="fschulz@lbl.gov",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "biopython",
        "pandas",
        "numpy",
        "scipy",
    ],
    entry_points={
        'console_scripts': [
            'nsgtree=nsgtree.main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'nsgtree': ['resources/models/*.hmm'],
    },
)
