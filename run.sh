#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${DIR:?}"

python_version="3.6.3"
python_folder="Python-${python_version}"
python_archive="${python_folder}.tar.xz"
python_dist="$(pwd)/python-dist"
#python_dist="${HOME}/python-dist"


if [ ! -e "${python_dist}/bin/python3" ]
then
    installed_gt_36=$(python -c "import sys; print(sys.version_info > (3,6))")
    echo "Setting up local Python..."
    if [ -n "$(command -v python3)" -a "${installed_gt_36}" = "True" ]
    then
        echo "Default Python version > 3.6, using venv..."
        python -m venv python-dist
    else
        echo "Default Python version < 3.6, using new local distribution..."
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
        fi
    fi

    echo "installing requirements..."
    export PIP_REQUIRE_VIRTUALENV=false; "${python_dist}/bin/pip3" install -q -r ./requirements.txt
fi

echo "run dbapi.py via hug..."
"${python_dist}/bin/hug" -f ./dbapi.py
