#!/bin/bash

CP=/bin/cp

########################################################################################
# commit formatting

function ci_commit_formatting_run {
    git remote add upstream https://github.com/micropython/micropython-lib.git
    git fetch --depth=100 upstream master
    # If the common ancestor commit hasn't been found, fetch more.
    git merge-base upstream/master HEAD || git fetch --unshallow upstream master
    # For a PR, upstream/master..HEAD ends with a merge commit into master, exclude that one.
    tools/verifygitlog.py -v upstream/master..HEAD --no-merges
}

########################################################################################
# package tests

MICROPYTHON=/tmp/micropython/ports/unix/build-standard/micropython

function ci_package_tests_setup_micropython {
    git clone https://github.com/micropython/micropython.git /tmp/micropython

    # build mpy-cross and micropython (use -O0 to speed up the build)
    make -C /tmp/micropython/mpy-cross -j CFLAGS_EXTRA=-O0
    make -C /tmp/micropython/ports/unix submodules
    make -C /tmp/micropython/ports/unix -j CFLAGS_EXTRA=-O0
}

function ci_package_tests_setup_lib {
    mkdir -p ~/.micropython/lib
    $CP micropython/ucontextlib/ucontextlib.py ~/.micropython/lib/
    $CP python-stdlib/fnmatch/fnmatch.py ~/.micropython/lib/
    $CP -r python-stdlib/hashlib-core/hashlib ~/.micropython/lib/
    $CP -r python-stdlib/hashlib-sha224/hashlib ~/.micropython/lib/
    $CP -r python-stdlib/hashlib-sha256/hashlib ~/.micropython/lib/
    $CP -r python-stdlib/hashlib-sha384/hashlib ~/.micropython/lib/
    $CP -r python-stdlib/hashlib-sha512/hashlib ~/.micropython/lib/
    $CP python-stdlib/shutil/shutil.py ~/.micropython/lib/
    $CP python-stdlib/tempfile/tempfile.py ~/.micropython/lib/
    $CP -r python-stdlib/unittest/unittest ~/.micropython/lib/
    $CP -r python-stdlib/unittest-discover/unittest ~/.micropython/lib/
    $CP unix-ffi/ffilib/ffilib.py ~/.micropython/lib/
    tree ~/.micropython
}

function ci_package_tests_run {
    for test in \
        micropython/drivers/storage/sdcard/sdtest.py \
        micropython/xmltok/test_xmltok.py \
        python-ecosys/requests/test_requests.py \
        python-stdlib/argparse/test_argparse.py \
        python-stdlib/base64/test_base64.py \
        python-stdlib/binascii/test_binascii.py \
        python-stdlib/collections-defaultdict/test_defaultdict.py \
        python-stdlib/functools/test_partial.py \
        python-stdlib/functools/test_reduce.py \
        python-stdlib/heapq/test_heapq.py \
        python-stdlib/hmac/test_hmac.py \
        python-stdlib/itertools/test_itertools.py \
        python-stdlib/operator/test_operator.py \
        python-stdlib/os-path/test_path.py \
        python-stdlib/pickle/test_pickle.py \
        python-stdlib/string/test_translate.py \
        unix-ffi/gettext/test_gettext.py \
        unix-ffi/pwd/test_getpwnam.py \
        unix-ffi/re/test_re.py \
        unix-ffi/sqlite3/test_sqlite3.py \
        unix-ffi/sqlite3/test_sqlite3_2.py \
        unix-ffi/sqlite3/test_sqlite3_3.py \
        unix-ffi/time/test_strftime.py \
        ; do
        echo "Running test $test"
        (cd `dirname $test` && $MICROPYTHON `basename $test`)
        if [ $? -ne 0 ]; then
            false # make this function return an error code
            return
        fi
    done

    for path in \
        micropython/ucontextlib \
        python-stdlib/contextlib \
        python-stdlib/datetime \
        python-stdlib/fnmatch \
        python-stdlib/hashlib \
        python-stdlib/pathlib \
        python-stdlib/quopri \
        python-stdlib/shutil \
        python-stdlib/tempfile \
        python-stdlib/time \
        python-stdlib/unittest-discover/tests \
        ; do
        (cd $path && $MICROPYTHON -m unittest)
        if [ $? -ne 0 ]; then false; return; fi
    done

    (cd micropython/usb/usb-device && $MICROPYTHON -m tests.test_core_buffer)
    if [ $? -ne 0 ]; then false; return; fi

    (cd python-ecosys/cbor2 && $MICROPYTHON -m examples.cbor_test)
    if [ $? -ne 0 ]; then false; return; fi
}

########################################################################################
# build packages

function ci_build_packages_setup {
    git clone https://github.com/micropython/micropython.git /tmp/micropython

    # build mpy-cross (use -O0 to speed up the build)
    make -C /tmp/micropython/mpy-cross -j CFLAGS_EXTRA=-O0

    # check the required programs run
    /tmp/micropython/mpy-cross/build/mpy-cross --version
    python3 /tmp/micropython/tools/manifestfile.py --help
}

function ci_build_packages_check_manifest {
    for file in $(find -name manifest.py); do
        echo "##################################################"
        echo "# Testing $file"
        extra_args=
        if [[ "$file" =~ "/unix-ffi/" ]]; then
            extra_args="--unix-ffi"
        fi
        python3 /tmp/micropython/tools/manifestfile.py $extra_args --lib . --compile $file
    done
}

function ci_build_packages_compile_index {
    python3 tools/build.py --micropython /tmp/micropython --output $PACKAGE_INDEX_PATH
}

function ci_build_packages_examples {
    for example in $(find -path \*example\*.py); do
        /tmp/micropython/mpy-cross/build/mpy-cross $example
    done
}

function ci_push_package_index {
    set -euo pipefail

    # Note: This feature is opt-in, so this function is only run by GitHub
    # Actions if the MICROPY_PUBLISH_MIP_INDEX repository variable is set to a
    # "truthy" value in the "Secrets and variables" -> "Actions"
    # -> "Variables" setting of the GitHub repo.

    PAGES_PATH=/tmp/gh-pages

    if git fetch --depth=1 origin gh-pages; then
        git worktree add ${PAGES_PATH} gh-pages
        cd ${PAGES_PATH}
        NEW_BRANCH=0
    else
        echo "Creating gh-pages branch for $GITHUB_REPOSITORY..."
        git worktree add --force ${PAGES_PATH} HEAD
        cd ${PAGES_PATH}
        git switch --orphan gh-pages
        NEW_BRANCH=1
    fi

    DEST_PATH=${PAGES_PATH}/mip/${GITHUB_REF_NAME}
    if [ -d ${DEST_PATH} ]; then
        git rm -r ${DEST_PATH}
    fi
    mkdir -p ${DEST_PATH}
    cd ${DEST_PATH}

    cp -r ${PACKAGE_INDEX_PATH}/* .

    git add .
    git_bot_commit "Add CI built packages from commit ${GITHUB_SHA} of ${GITHUB_REF_NAME}"

    if [ "$NEW_BRANCH" -eq 0 ]; then
        # A small race condition exists here if another CI job pushes to
        # gh-pages at the same time, but this narrows the race to the time
        # between these two commands.
        git pull --rebase origin gh-pages
    fi
    git push origin gh-pages

    INDEX_URL="https://${GITHUB_REPOSITORY_OWNER}.github.io/$(echo ${GITHUB_REPOSITORY} | cut -d'/' -f2-)/mip/${GITHUB_REF_NAME}"

    echo ""
    echo "--------------------------------------------------"
    echo "Uploaded package files to GitHub Pages."
    echo ""
    echo "Unless GitHub Pages is disabled on this repo, these files can be installed remotely with:"
    echo ""
    echo "mpremote mip install --index ${INDEX_URL} PACKAGE_NAME"
    echo ""
    echo "or on the device as:"
    echo ""
    echo "import mip"
    echo "mip.install(PACKAGE_NAME, index=\"${INDEX_URL}\")"
}

function ci_cleanup_package_index()
{
    if ! git fetch --depth=1 origin gh-pages; then
        exit 0
    fi

    # Argument $1 is github.event.ref, passed in from workflow file.
    #
    # this value seems to be a REF_NAME, without heads/ or tags/ prefix. (Can't
    # use GITHUB_REF_NAME, this evaluates to the default branch.)
    DELETED_REF="$1"

    if [ -z "$DELETED_REF" ]; then
        echo "Bad DELETE_REF $DELETED_REF"
        exit 1  # Internal error with ref format, better than removing all mip/ directory in a commit
    fi

    # We need Actions to check out default branch and run tools/ci.sh, but then
    # we switch branches
    git switch gh-pages

    echo "Removing any published packages for ${DELETED_REF}..."
    if [ -d mip/${DELETED_REF} ]; then
        git rm -r mip/${DELETED_REF}
        git_bot_commit "Remove CI built packages from deleted ${DELETED_REF}"
        git pull --rebase origin gh-pages
        git push origin gh-pages
    else
        echo "Nothing to remove."
    fi
}

# Make a git commit with bot authorship
# Argument $1 is the commit message
function git_bot_commit {
    # Ref https://github.com/actions/checkout/discussions/479
    git config user.name 'github-actions[bot]'
    git config user.email 'github-actions[bot]@users.noreply.github.com'
    git commit -m "$1"
}
