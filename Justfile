# just has no idiom for setting a default value for an environment variable
# so we shell out, as we need VIRTUAL_ENV in the justfile environment
export VIRTUAL_ENV  := `echo ${VIRTUAL_ENV:-.venv}`

export BIN := VIRTUAL_ENV + "/bin"
export PIP := BIN + "/python -m pip"
# enforce our chosen pip compile flags
export COMPILE := BIN + "/pip-compile --allow-unsafe --generate-hashes"


test_args := "tests"


# list available commands
default:
    @{{ just_executable() }} --list


# clean up temporary files
clean:
    rm -rf .venv


# ensure valid virtualenv
virtualenv:
    #!/usr/bin/env bash
    # allow users to specify python version in .env
    PYTHON_VERSION=${PYTHON_VERSION:-python3}

    # create venv and upgrade pip
    test -d $VIRTUAL_ENV || { $PYTHON_VERSION -m venv $VIRTUAL_ENV && $PIP install --upgrade pip; }

    # ensure we have pip-tools so we can run pip-compile
    test -e $BIN/pip-compile || $PIP install pip-tools


# update requirements.prod.txt if requirement.prod.in has changed
requirements-prod: virtualenv
    #!/usr/bin/env bash
    # exit if .in file is older than .txt file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test requirements.prod.in -nt requirements.prod.txt || exit 0
    $COMPILE --output-file=requirements.prod.txt requirements.prod.in


# update requirements.dev.txt if requirements.dev.in has changed
requirements-dev: requirements-prod
    #!/usr/bin/env bash
    # exit if .in file is older than .txt file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test requirements.dev.in -nt requirements.dev.txt || exit 0
    $COMPILE --output-file=requirements.dev.txt requirements.dev.in


# ensure prod requirements installed and up to date
prodenv: requirements-prod
    #!/usr/bin/env bash
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.prod.txt -nt $VIRTUAL_ENV/.prod || exit 0

    $PIP install -r requirements.prod.txt
    touch $VIRTUAL_ENV/.prod

# ensure dev requirements installed and up to date
devenv: prodenv requirements-dev 
    #!/usr/bin/env bash
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.dev.txt -nt $VIRTUAL_ENV/.dev || exit 0

    $PIP install -r requirements.dev.txt
    touch $VIRTUAL_ENV/.dev


# upgrade dev or prod dependencies (all by default, specify package to upgrade single package)
upgrade env package="": virtualenv
    #!/usr/bin/env bash
    opts="--upgrade"
    test -z "{{ package }}" || opts="--upgrade-package {{ package }}"
    $COMPILE $opts --output-file=requirements.{{ env }}.txt requirements.{{ env }}.in


# runs the format (black), sort (isort) and lint (flake8) check but does not change any files
check: devenv
    $BIN/black --check .
    $BIN/isort --check-only --diff .
    $BIN/flake8

# fix formatting and import sort ordering
fix: devenv
    $BIN/black .
    $BIN/isort .

# run the tests
test *ARGS: devenv
    echo "Run tests"
    $BIN/python -m pytest \
        --cov=tretools \
        --cov-report=html \
        --cov-report=term-missing:skip-covered \
        {{ ARGS }}

# Run the dev project
run: devenv
    echo "Not implemented yet"

# bump the version. patch by default, specify major or minor to bump those
bump *ARGS: devenv
    echo "Bump Version to {{ ARGS }}"
    bump2version {{ ARGS }}
