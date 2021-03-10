#!/bin/bash


user=$(whoami)
BASE_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function check_inst_tools() {
	pip3 &> /dev/null
	if [ ! $? == 0 ]; then
		echo '>>> please install pip3 (python3-pip)'
		return 1
	fi
	python3 -c 'import distutils' &> /dev/null
	if [ $? == 1 ]; then
		echo '>>> please install python distutils module'
		echo '>>> ie: pip3 install distutils'
		return 1
	fi
	python3 -c 'import distutils.util' &> /dev/null
	if [ $? == 1 ]; then
		echo '>>> please install python distutils.util module'
		echo '>>> ie: pip3 install distutils.util'
		return 1
	fi
	curl &> /dev/null
	if [ ! $? == 2 ]; then
		echo '>>> please install curl'
		return 1
	fi
	unzip &> /dev/null
	if [ ! $? == 0 ]; then
		echo '>>> please install unzip'
		return 1
	fi
	sudo &> /dev/null
	if [ ! $? == 1 ]; then
		echo '>>> please install sudo'
		return 1
	fi
}

function spinner(){
	spinner="/|\\-/|\\-"
	while :
		do
			for i in `seq 0 7`
				do
					echo -n "${spinner:$i:1}"
					echo -en "\010"
					sleep 0.2
				done
		done
}

function setup_folders(){
	mkdir -p ~/.ssh/pcli
	sudo mkdir -p /etc/pcli/ansible/playbooks
	sudo mkdir -p /etc/pcli/terraform
	sudo mkdir -p /var/log/pcli
	sudo chown -R "$user:$user" /etc/pcli
	sudo chown -R "$user:$user" /var/log/pcli
	FOLDERS_ARRAY=( ~/.ssh/pcli/ /etc/pcli/ansible/playbooks/ /etc/pcli/terraform/ /var/log/pcli/ )
	for folder in "${FOLDERS_ARRAY[@]}"; do
		if [ -d "$folder" ]; then
			echo ">>> $folder created"
		else
			echo ">>> $folder missing"
			return 1
		fi
	done
}

function inst_pipenv_ansible(){
	printf '>>> installing ansible and pipenv    '
	spinner &
	SPINNER_PID=$!
	trap "kill -9 $SPINNER_PID" `seq 0 15`
	python3 -m pip install --user --no-warn-script-location ansible pipenv passlib >> /var/log/pcli/pcli.log
	kill -9 $SPINNER_PID
	wait $SPINNER_PID 2> /dev/null
	PYTHON_BIN_PATH="$(python3 -m site --user-base)/bin"
	PATH="$PATH:$PYTHON_BIN_PATH"
	pipenv &> /dev/null
	if [ $? == 127 ]; then
	      echo '>>> something wrong during pipenv installation - please check /var/pcli/pcli.log'
	      return 1
	fi
	echo; echo '>>> pipenv installed'
	ansible &> /dev/null
	if [ $? == 127 ]; then
	      echo '>>> something wrong during ansible installation - please check /var/pcli/pcli.log'
	      return 1
	fi
	echo '>>> ansible installed'
}

function inst_terraform(){
	if [ ! -f '/usr/bin/terraform' ]; then
		printf '>>> downloading and installing terraform    '
		spinner &
		SPINNER_PID=$!
		trap "kill -9 $SPINNER_PID" `seq 0 15`
		install -d -m 775 -o "$user" /tmp/pcli
		mkdir -p /tmp/pcli && cd "$_"
		curl -s https://releases.hashicorp.com/terraform/0.13.3/terraform_0.13.3_linux_amd64.zip --output terraform_0.13.3_linux_amd64.zip >> /var/log/pcli/pcli.log
		unzip terraform_0.13.3_linux_amd64.zip -d /tmp/pcli/ >> /var/log/pcli/pcli.log
		chmod +x terraform
		sudo mv terraform /usr/bin/terraform
		cd - > /dev/null
		rm -rf /tmp/pcli
		kill -9 $SPINNER_PID
		wait $SPINNER_PID 2> /dev/null
	fi
	if [ ! -f '/usr/bin/terraform' ]; then
	      echo '>>>'; echo '>>> something wrong during terraform installation - please check /var/pcli/pcli.log'
	      return 1
	fi
	echo; echo '>>> terraform installed'
}

function config_setup(){
	cp "$BASE_PATH/config/ansible/ansible.cfg" /etc/pcli/ansible/
	cp "$BASE_PATH/config/ansible/playbooks/edit_user_pwd.yml" /etc/pcli/ansible/playbooks/
	cp "$BASE_PATH/config/ansible/playbooks/pnode_package.yml" /etc/pcli/ansible/playbooks/
	cp "$BASE_PATH/config/ansible/playbooks/sys_config.yml" /etc/pcli/ansible/playbooks/
	cp "$BASE_PATH/config/terraform/inst_config.json" /etc/pcli/terraform/
	cp "$BASE_PATH/config/terraform/variables.tf.json.orig" /etc/pcli/terraform/
	cp "$BASE_PATH/config/terraform/main.tf.orig" /etc/pcli/terraform/
	cp "$BASE_PATH/config/terraform/output.tf.orig" /etc/pcli/terraform/
	FILES_ARRAY=("/etc/pcli/ansible/ansible.cfg" "/etc/pcli/ansible/playbooks/edit_user_pwd.yml"
		"/etc/pcli/ansible/playbooks/pnode_package.yml" "/etc/pcli/ansible/playbooks/sys_config.yml"
		"/etc/pcli/terraform/inst_config.json" "/etc/pcli/terraform/variables.tf.json.orig"
		"/etc/pcli/terraform/main.tf.orig" "/etc/pcli/terraform/output.tf.orig")
	for file in "${FILES_ARRAY[@]}"; do
		if [ -f "$file" ]; then
			echo ">>> $file moved in path"
		else
			echo ">>> $file not moved in path"
			return 1
		fi
	done
	echo '>>> all config files moved in path'
}

function build_pipenv_env(){
	printf '>>> building pipenv environment    '
	spinner &
	SPINNER_PID=$!
	trap "kill -9 $SPINNER_PID" `seq 0 15`
	cd "$BASE_PATH"
	pipenv install >> /var/log/pcli/pcli.log 2>&1
	kill -9 $SPINNER_PID
	wait $SPINNER_PID 2> /dev/null
	echo; echo '>>> pipenv environment built'
}

function setup_bashrc(){
	if ! grep -q "if [ -r ~/.bashrc ]; then" ~/.bash_profile > /dev/null 2>&1 /dev/null ; then
		if [ ! -f ~/.bash_profile ]; then
			echo '>>> ~/.bash_profile not found'
			touch ~/.bash_profile
		fi
		echo "if [ -r ~/.bashrc ]; then" >> ~/.bash_profile
		echo "    source ~/.bashrc" >> ~/.bash_profile
		echo "fi" >> ~/.bash_profile
		echo '>>> ~/.bash_profile created and edited'
	fi
	if ! grep -q "pcli" ~/.bashrc > /dev/null 2>&1 /dev/null; then
		if [ ! -f ~/.bashrc ]; then
			touch ~/.bashrc
		fi
		echo "alias pcli='$(cd $BASE_PATH; pipenv --venv)/bin/python $BASE_PATH/cli.py'" >> ~/.bashrc
		source ~/.bashrc
		echo '>>> bashrc edited'
		echo '>>> pcli moved in path'
	fi
}

function start_checks(){
	if check_inst_tools; then
		main
	else return 1
	fi
}

function main(){
	if ! setup_folders; then
		return 1
	fi
	if ! inst_pipenv_ansible; then
		return 1
	fi
	if ! inst_terraform; then
		return 1
	fi
	if ! config_setup; then
		return 1
	fi
	build_pipenv_env

	cd > /dev/null

	setup_bashrc

	echo; echo;
	echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
	echo '>>> installation finished!'
	echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
	echo; echo;
}

start_checks
