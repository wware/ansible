# Ansible Vibes

Ansible manages groups of Unix machines by putting the information about the
machines into machine-readable form and then applying commands and other
operations to any chosen subset of those machines.

Ansible takes an inventory file, which is a group of machine descriptions,
in either INI or YAML format. I find YAML to be more readable and provide
more options. With these descriptions, Ansible can perform a variety of
useful operations on selected groups of machines.

The prerequisites for using Ansible are
- it needs to be installed on your desktop/laptop - it does not need
  to be installed on the target machines
- all the target machines must accept SSH connections
- you need a working inventory file describing all target machines

If you have some very repeatable way (ideally automated) to get a machine to this
minimal point, then Ansible can take care of any further machine configuration, and
voila, you've got
[Infrastructure-as-Code](https://en.wikipedia.org/wiki/Infrastructure_as_code)
with all the benefits that accrue therefrom.
Ansible can deploy the same code on multiple platforms: do development in
[Docker](https://en.wikipedia.org/wiki/Docker_(software)) or
[Xen](https://en.wikipedia.org/wiki/Xen) and deploy to
[Raspberry Pi](https://en.wikipedia.org/wiki/Raspberry_Pi) or
[AWS](https://en.wikipedia.org/wiki/Amazon_Web_Services) or 
[Kubernetes](https://kubernetes.io/) or whatever Unixy metal you have around.

Ansible can take commands one at a time on the command line, or it can
take batches of instructions in files called "playbooks". I'll discuss
playbooks later.

# Ad-hoc commands

This is the "Hello World" command for Ansible.

    ansible all -a "echo Hello World"

This will SSH into all the target machines in the inventory file and
make them send back "Hello World". If any machines are not reachable
you'll see warnings about that. This is equivalent to typing:

    ssh <user>@<host> echo Hello World

for every machine in the inventory file, but it's a lot less typing.

You can run a command on a bunch of machines like this:

    ansible -i inventory.yaml all -a "echo HELLO"

The "`-i inventory.yaml`" part specifies an inventory file. If you use the
default `/etc/ansible/hosts`, you can omit this.

Some commands are so popular that people have written Ansible modules for them,
for instance

    ansible all -m ping

## Selecting groups of machines

To choose a subset of machines, we replace "all" with something that says
which machines we want. The simplest thing is to use one of the groups in
the inventory file. In our inventory file, the groups are:

    web - machines that will run a web application
    db - machines that will run a database

To address the machines in these groups, we can type commands like

    ansible web -a 'do some stuff'
    ansible db -a 'do some stuff'

We can also use combinations of groups

    'group1:group2' - machines that are in group1 OR in group2
    'group1:&group2' - machines that are in group1 AND ALSO in group2
    'group1:!group2' - machines that are in group1 AND NOT in group2

This would be useful if we have more groups, or some subgroups. Groups
can be overlapping or disjoint.

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

# Host and group variables

Ansible uses Jinja2-style templating for variables in commands. Our inventory
file defines some database-related variables for the "dev" group which are used
here.

    ansible db -m shell -a "echo 'show databases;' | mysql -h {{db_host}} -u {{db_user}} --password={{db_passwd}}"

There are also variables for individual hosts or machines. Each machine has an
`ansible_ssh_user` variable which Ansbile uses to put together SSH commands. The
workers all have `workdir` and `tasks` variables. These can be used with the same
kind of templating.

# Ansible modules

The `-m shell` argument above means that instead of running commands as we've normally
done, we are sending everything in double quotes to a shell command line, which
allows us to use the Unix pipe in the middle of the command. This uses the `shell`
module.

The `-a "foo=this bar=that xyzzy=other"` piece is how arguments are passed to the module,
and this is actually taken from the INI syntax mentioned earlier. In playbooks, these
arguments are usually done as YAML lists.

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

## Pushing and pulling files

Here is a command to push a new version of an HTML file to some web machines. This uses
[the `copy` module](https://docs.ansible.com/ansible/latest/modules/copy_module.html).

    ansible web -m copy \
        -a 'src=path/on/laptop/template.html dest={{workdir}}/foo/bar/template.html'

When pulling files you use
[the `fetch` module](https://docs.ansible.com/ansible/latest/modules/fetch_module.html).
If you're pulling files from many different machines, you can use a variable to tell
them apart, like this.

    $ ansible web -m fetch -a 'src={{workdir}}/foo/bar/template.html dest=template-{{inventory_hostname}}'

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

# Running playbooks

Here is a very simple playbook. This playbook updates all the Linux machines on
all our stacks to make sure they are all using East Coast time. This is done by
first moving the existing `/etc/localtime` file out of the way, and then creating
a symbolic link to the `/usr/share/zoneinfo/America/New_York` file.

The playbook first specifies what hosts it should work with. The next line,
`become: true`, means that we run these commands using `sudo`. The last command
is a debugging step where we print the standard output of the previous command
to show that the time zone has been updated correctly.

    - hosts: web
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

We can run the playbook simply by typing:

    ansible-playbook playbook.yml

If we have more groups, we can make a more specific choice of machines using the
"--limit" option.
