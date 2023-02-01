#!/bin/bash

########################################################################################
# code formatting

function ci_code_formatting_setup {
    sudo apt-add-repository --yes --update ppa:pybricks/ppa
    sudo apt-get install uncrustify
    pip3 install black
    uncrustify --version
    black --version
}

function ci_code_formatting_run {
    tools/codeformat.py -v
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
        python3 /tmp/micropython/tools/manifestfile.py --lib . --compile $file
    done
}

function ci_build_packages_compile_index {
    python3 tools/build.py --micropython /tmp/micropython --output /tmp/micropython-lib-deploy
}
