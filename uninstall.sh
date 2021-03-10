#!/bin/bash


BASE_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function confirm_uninstall(){
	while :; do
		read -p '>>> do you really want to uninstall pcli and remove its files? y/n ' answer
		case $answer in
			[Yy]* ) return 0;;
			[Nn]* ) return 1;;
			* ) echo '>>> please answer y or n';;
		esac
	done
}

function remove_folders(){
        rm -r ~/.ssh/pcli &> /dev/null
        sudo rm -r /etc/pcli/ &> /dev/null
        sudo rm -r /var/log/pcli &> /dev/null
        FOLDERS_ARRAY=( ~/.ssh/pcli/ /etc/pcli/ /var/log/pcli/ )
        for folder in "${FOLDERS_ARRAY[@]}"; do
                if [ ! -d "$folder" ]; then
                        echo ">>> $folder deleted"
                else
                        echo ">>> error deleting $folder"
                fi
        done
}

function remove_pipenv_env(){
        grep -v "$(cd $BASE_PATH; pipenv --venv)" ~/.bashrc > ~/.bashrc_tmp
        mv ~/.bashrc_tmp ~/.bashrc &> /dev/null
        rm ~/.bashrc_tmp &> /dev/null
        source ~/.bashrc
	rm -r "$(cd $BASE_PATH; pipenv --venv)" &> /dev/null
        echo '>>> bashrc edited'
        echo '>>> pcli removed from path'
}

function verify_uninstall(){
        pcli &> /dev/null
        if [ ! $? == 127 ]; then
                echo '>>> error while uninstalling'
                return 1
        fi
}

function main(){

        if ! confirm_uninstall; then
		return 1
	fi

        remove_folders
        remove_pipenv_env

        if ! verify_uninstall; then
                return 1
        fi

        echo; echo;
        echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        echo '>>> uninstall finished!'
        echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        echo; echo;
}

main
