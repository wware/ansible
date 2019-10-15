# Ansible Tutorial

Ansible manages groups of Unix machines by putting the information about the
machines into machine-readable form and then applying commands and other
operations to any chosen subset of those machines.

# Ansible requirements

In order to work, Ansible requires an inventory file which lists all the machines
being managed. Each machine must have
* a Unix-like operating system (Cygwin is OK)
* an IP address and/or hostname on the network
* a user with sudo privileges
* a working SSHD service

If you have some very repeatable way (ideally automated) to get a machine to this
minimal point, then Ansible can take care of any further machine configuration, and
voila, you've got
[Infrastructure-as-Code](https://en.wikipedia.org/wiki/Infrastructure_as_code)
with all the benefits that accrue therefrom.

## Managing multiple platforms

Ansible can deploy the same code on multiple platforms: do development in
[Docker](https://en.wikipedia.org/wiki/Docker_(software)) or
[Xen](https://en.wikipedia.org/wiki/Xen) and deploy to
[Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi) or
[AWS](https://en.wikipedia.org/wiki/Amazon_Web_Services) or 
[Kubernetes](https://kubernetes.io/) or whatever Unixy metal you have around.
Just get everybody to an equivalent baseline and take it from there.

# The inventory file

Inventory files can have either a YAML or an INI format.

The file describing our stacks looks like this. Here I've only filled
in the full details for the staging stack.

    all:
      children:
        master:
          hosts:
            amber-buildbot-5:
            amber-buildbot-2:
            linux_buildbot.staticqa.veracode.io:
        production:
          ...
        staging:
          hosts:
            amber-buildbot-2:        # a Linux machine
              ansible_ssh_user: buildbot
            amber-bbot-3:            # a Cygwin machine
              ram: 64
              ansible_ssh_user: enguser
              workdir: /cygdrive/e/buildbot/heimdall
              tasks: [manual, mergetest, smoketest]
            amber-bbot-6:            # more Cygwin
              ram: 128
              ansible_ssh_user: enguser
              workdir: /cygdrive/c/buildbot/rogue
              tasks: [test-worker]
        prod_linux:
          ...

Reserved words:
* `hosts` - what follows is a list of host machines (which may include host variables)
* `childen` - what follows is a list of subgroups within this group
* `vars` - what follows is a list of group variables

Subgroups will have their own `hosts`, `children` and `vars` sections.

A machine can appear in multiple groups. Variables will come from
all the machine's groups, with
[precedence rules](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#ansible-variable-precedence),
but it's good practice to define a variable in only one place to avoid confusion.

Machines are grouped into four semi-overlapping groups: `master`,
`production`, `staging`, and `prod_linux`. Because Ansible can work with
classifications like "this group AND that group" or "this group AND NOT that group",
we can easily specify that we want to address all production workers, or
the master on staging, or all the machines in the `prod_linux` stack, etc.

If you're going to do much with Ansible, it would make sense to create a
`/etc/ansible/hosts` file like this one on your machine.

Example INI-style inventory file:

    [master]
    35.153.159.105  ansible_ssh_user=buildbot
    [worker]
    18.232.97.176  ansible_ssh_user=ec2-user workdir=/home/ec2-user tasks=test-worker
    54.92.185.209  ansible_ssh_user=ec2-user workdir=/home/ec2-user tasks=test-worker
    34.238.169.197  ansible_ssh_user=ec2-user workdir=/home/ec2-user tasks=test-worker
    3.94.204.183  ansible_ssh_user=ec2-user workdir=/home/ec2-user tasks=smoketest,mergetest
    54.81.100.180  ansible_ssh_user=ec2-user workdir=/home/ec2-user tasks=smoketest,mergetest

Here the groups are `master` and `worker`, but can be whatever you want.
Each host is one line in the file, starting with a hostname or IP address,
followed by host variables. These variables can be used in commands and playbooks.

# Ad-hoc commands

You can run a command on all our machines like this:

    ansible -i inventory.yaml all -a "echo HELLO"

A command to run on just the masters:

    ansible -i inventory.yaml master -a "echo HELLO"

The "`-i inventory.yaml`" part specifies an inventory file. If you use the
default `/etc/ansible/hosts`, you can omit this. For brevity I'll omit it for
the rest of this document.

Some commands are so popular that people have written Ansible modules for them,
for instance

    ansible all -m ping

The OR operator for groups in Ansible is the colon. This will run a command
on the machines that are masters OR are on the staging stack.

    ansible 'staging:master' -a "echo 3"

The AND operator for groups in Ansible is colon-ampersand. This will run a command
on the one machine that is a master and is on the staging stack.

    ansible 'staging:&master' -a "echo 3"

To run a command on the workers on the staging stack, we select all machines 
that are on staging and are NOT a master.

    ansible 'staging:!master' -a "echo 3"

## More example Ansible commands

    # Ping local machine
    ansible -c local -m ping all

    # Ping remote machine
    ansible -c local -m ping amber-bbot-3

    # Run a command on a remote machine
    ansible <hostname> -m shell -a "echo HELLO"

    # Identify local machine
    ansible localhost -a whoami

    # Identify remote servers (if any)
    ansible all -a whoami

    # Gather facts about local machine
    ansible -m setup localhost

    # Gather facts about remote servers
    ansible -m setup 'dev:&linux' -u ec2-user

    # How long has host been running since last restart?
    ansible all -m command -a uptime

## Jinja2 templating within an ad-hoc command

    # last three characters of user name, Python expressions work
    ansible all -m debug -a "msg={{ ansible_ssh_user[-3:] }}"

    # select ansible module based on user name
    ansible -c local -m "{% if ansible_ssh_user == 'ec2-user' %}debug{% else %}fail{% endif %}" all

# Running playbooks

This is a pretty minimal playbook file. It starts by specifying which machines
it's supposed to run on, and then it runs some tasks. The "debug" task prints
information. Here we are taking stdout from the previous (hello) task and also
looking at a variable from the inventory file.

    - hosts: staging
      tasks:
      - name: my little playbook task
        shell: echo $USER
        register: hello
      - debug: msg="{{ hello.stdout }}, {{ ansible_ssh_user }}"

Another little example, this one sets the time zones on EC2 Linux instances for
East Coast time.

    - hosts: linux
      become: true
      tasks:
      - name: move the /etc/localtime file aside
        shell: mv -f /etc/localtime /etc/localtime.old
      - name: new /etc/localtime, EST5EDT
        file:
          src: "/usr/share/zoneinfo/America/New_York"
          dest: "/etc/localtime"
          state: link
      - name: tell the current date
        shell: date
        register: date
      - debug: msg="{{ date.stdout }}"

If you create a YAML file like this and call it `playbook.yml`, you can run it
like this.

    ansible-playbook playbook.yml

You can use `--limit` to restrict it to a subset of the specified hosts.

    ansible-playbook playbook.yml --limit master

# Ansible modules

The Ansible user community has written tons of modules for different
tasks and platforms,
[listed by category](https://docs.ansible.com/ansible/latest/modules/modules_by_category.html),
and a 
[flattened list](https://docs.ansible.com/ansible/latest/modules/list_of_all_modules.html).

[This page](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html)
tells how to develop your own Ansible module, which is done in Python.

Here are a few of the most useful modules.
* [shell](https://docs.ansible.com/ansible/latest/modules/shell_module.html):
  run shell commands on the host
* [file](https://docs.ansible.com/ansible/latest/modules/file_module.html):
  copy files or create symlinks on the host, or change attributes,
  or other stuff with files
* [copy](https://docs.ansible.com/ansible/latest/modules/copy_module.html):
  push a file to a host
* [fetch](https://docs.ansible.com/ansible/latest/modules/fetch_module.html):
  pull a file from a host

Surprisingly, among the various
[database-related modules](https://docs.ansible.com/ansible/latest/modules/list_of_database_modules.html),
there is one for
[running queries on PostgreSQL](https://docs.ansible.com/ansible/latest/modules/postgresql_query_module.html)
but no such module for MySQL. So maybe I'll work on that at some point, probably
starting by cloning the PostgreSQL query module and tweaking it.