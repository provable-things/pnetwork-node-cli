#!/bin/bash


user=$(whoami)
BASE_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

function check_inst_tools() {
	unzip &> /dev/null
	if [ ! $? == 0 ]; then
		echo '>>> please install unzip'
	fi
	sudo &> /dev/null
	if [ ! $? == 1 ]; then
		echo '>>> please install sudo'
	fi
}

check_inst_tools

install -d -m 700 -o $user ~/.ssh/pcli
sudo install -d -m 775 -o $user /etc/pcli/
echo '>>> folder /etc/pcli/ created'
sudo install -d -m 775 -o $user /etc/pcli/ansible/
echo '>>> folder /etc/pcli/ansible created'
sudo install -d -m 775 -o $user /etc/pcli/ansible/playbooks
echo '>>> folder /etc/pcli/ansible/playbooks created'
sudo install -d -m 775 -o $user /etc/pcli/terraform
echo '>>> folder /etc/pcli/terraform created'
sudo install -d -m 775 -o $user /var/log/pcli
echo '>>> folder /var/log/pcli/ created'

touch /var/log/pcli/pcli.log
echo '>>> log file /var/log/pcli/pcli.log created'

echo '>>> installing pip3'
curl -sS https://bootstrap.pypa.io/get-pip.py | python3 >> /var/log/pcli/pcli.log 2>&1
export PATH="$HOME/.local/bin:$PATH"
echo '>>> pip3 installed'

echo '>>> installing ansible and pipenv'
pip3 install --user --no-warn-script-location ansible pipenv passlib >> /var/log/pcli/pcli.log
echo '>>> ansible and pipenv installed'

echo '>>> downloading and installing terraform'
install -d -m 775 -o $user /tmp/pcli
mkdir -p /tmp/pcli && cd $_
curl -s https://releases.hashicorp.com/terraform/0.13.3/terraform_0.13.3_linux_amd64.zip --output terraform_0.13.3_linux_amd64.zip >> /var/log/pcli/pcli.log
unzip terraform_0.13.3_linux_amd64.zip -d /tmp/pcli/ >> /var/log/pcli/pcli.log
chmod +x terraform
sudo mv terraform /usr/bin/terraform
cd - > /dev/null
rm -rf /tmp/pcli
echo '>>> terraform installed'

cp "$BASE_PATH/config/ansible/ansible.cfg" /etc/pcli/ansible/
cp "$BASE_PATH/config/ansible/playbooks/edit_user_pwd.yml" /etc/pcli/ansible/playbooks/
cp "$BASE_PATH/config/ansible/playbooks/pnode_package.yml" /etc/pcli/ansible/playbooks/
cp "$BASE_PATH/config/ansible/playbooks/sys_config.yml" /etc/pcli/ansible/playbooks/
cp "$BASE_PATH/config/terraform/inst_config.json" /etc/pcli/terraform/
cp "$BASE_PATH/config/terraform/variables.tf.json.orig" /etc/pcli/terraform/
cp "$BASE_PATH/config/terraform/main.tf.orig" /etc/pcli/terraform/
cp "$BASE_PATH/config/terraform/output.tf.orig" /etc/pcli/terraform/
echo '>>> all config files moved in path'

echo '>>> building pipenv environment'
cd "$BASE_PATH"
pipenv install >> /var/log/pcli/pcli.log 2>&1
echo '>>> pipenv environment built'
cd > /dev/null
if [ ! -f ./bash_profile ]; then
	echo '>>> ~/.bash_profile not found'
        echo "if [ -r ~/.bashrc ]; then" >> ~./bash_profile
        echo "    source ~/.bashrc" >> ~./bash_profile
        echo "fi" >> ~./bash_profile
	echo '>>> ~/.bash_profile created and edited'
fi
if ! grep -q "pcli" ~/.bashrc || \
        [ ! -f ~/.bashrc ]; then
                echo "alias pcli='$(cd $BASE_PATH; pipenv --venv)/bin/python $BASE_PATH/cli.py'" >> ~/.bashrc
                source ~/.bashrc
		echo '>>> bashrc edited'
                echo '>>> pcli moved in path'
fi
echo; echo;
echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
echo '>>> installation finished!'
echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
echo; echo;
