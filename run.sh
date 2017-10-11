#!/usr/bin/env bash

python_version="3.6.3"
python_folder="Python-${python_version}"
python_archive="${python_folder}.tar.xz"
python_dist="$(pwd)/python-dist"
#python_dist="${HOME}/python-dist"

if [ ! -e "${python_dist}/bin/python3" ]
then
    echo "Setting up local Python..."
    if [ ! -e "./${python_archive}" ]
    then
        echo "get ${python_archive} from web..."
        wget "https://www.python.org/ftp/python/${python_version}/${python_archive}"
    fi

    if [ ! -d "./${python_folder}" ]
    then
        echo "extracting ${python_archive}..."
        tar xf "./${python_archive}"
    fi
fi

if [ ! -d "${python_dist}" ]
then
    cd "./${python_folder}"

    if [ ! -e "Makefile" ]
    then
        # TODO fix prefix containing spaces?
        echo "make ${python_folder}..."
        ./configure --prefix="${python_dist}" --silent
        make --silent > /dev/null 2> /dev/null
    fi

    echo "make install ${python_folder}..."
    make install --silent > /dev/null 2> /dev/null
    cd ..

    export PIP_REQUIRE_VIRTUALENV=false; "${python_dist}/bin/pip3" install -q -r ./requirements.txt
fi

echo "run dbapi.py via hug..."
hug -f ./dbapi.py
