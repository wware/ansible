# Messing with Ansible and Docker

Set up a Docker image and do a quick test of it.

    docker build -t simple_flask:dockerfile .
    docker run -p 5000:5000 simple_flask:dockerfile python hello.py
    docker run -it -p 5000:5000 -p 22:8022 simple_flask:dockerfile bash

My actual intention is to learn [Ansible](https://docs.ansible.com/ansible/latest/user_guide/intro_getting_started.html).
But in order to run Ansible you need Docker, unless you happen to have a rackful of machines at your disposal which I do not.

## Basic tinkering

Look at [these instructions](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-ansible-on-ubuntu-16-04)
to install Ansible properly.
[More Ansible stuff here](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-ansible-on-ubuntu-14-04)
but it does not talk about using Docker.
Wait, [this one](https://www.webcodegeeks.com/devops/docker-ansible-example/) might work. Honorable mention for
[1](http://www.googlinux.com/ansible-getting-started/) and
[2](http://www.googlinux.com/creating-docker-container-using-ansible/index.html).

Working from [this page](https://www.webcodegeeks.com/devops/docker-ansible-example/), I have
started to make Ansible do some things. Here we start and then stop three HTTP servers.

    ansible-playbook docker_go.yml
    curl http://127.0.0.1:5000/   ==> value1
    curl http://127.0.0.1:5001/   ==> value2
    curl http://127.0.0.1:5002/   ==> value3
    ansible-playbook docker_stop.yml

So that is pretty cool already, and I know Ansible has a bunch more stuff like applying names to groups of
machines (webserver, database, etc) so that you can run bunches of commands on them. Slick.

## Get SSH running on the Docker instances

Ansible needs SSH to connect to the instances. So I need an SSHD server running on them, and I need to
be able to find out their IP addresses. Let's figure that out.
