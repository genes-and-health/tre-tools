# tretools

`tretools` is a Python package tailored for data scientists and researchers looking to streamline the process of running codelist numbers against various datasets in the Genes and Health TRE. It also provides a variety of data cleaning functions to prepare your datasets for analysis.

## Getting Started
### Prerequisites

Before installing `tretools`, ensure you have the following installed:
- Python 3.8+
- pip 
- pip-tools for managing dependencies
- Just

### Installation
The package is being installed into the TRE and can be used in the usual way there. 

If you wish to install it locally, you can do so in two ways. 

#### 1. Install from GitHub
```
pip install git+https://github.com/genes-and-health/tre-tools.git
```

#### 2. Install from local directory in order to make changes to the package
Clone the repo:
```
git clone https://github.com/genes-and-health/tre-tools.git
```

Install the package in editable mode:
```
pip install -e <path-to-tre-tools>
```

## Usage
There are two building blocks to `tretools`:

1. `Codelist`
2. `Dataset`

### Codelists
A `Codelist` is a collection of codelist numbers that can be used to run against a dataset. There are 3 types of codelists:

1. `Codelist` - a codelist of numbers