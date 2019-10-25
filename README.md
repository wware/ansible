# Ansible Vibes

I've been looking into Ansible as a tool for managing Buildbot stacks
and I've found it very useful. It does the same things as some of the
scripts I've written myself, more cleanly and reliably. So I think,
where appropriate, we should adopt it.

Ansible takes an inventory file, which is a group of machine descriptions,
in either INI or YAML format. I find YAML to be more readable and provide
more options. With these descriptions, Ansible can perform a variety of
useful operations on selected groups of machines.

The prerequisites for using Ansible are
- it needs to be installed on your desktop/laptop - it does not need
  to be installed on the target machines
- all the target machines must accept SSH connections
- you need a working inventory file describing all target machines

Our current inventory file is
[here](https://gitlab.laputa.veracode.io/wware/ansible/blob/master/etc_ansible_hosts).
To use it, copy it to `/etc/ansible/hosts` on your desktop/laptop.

Ansible can take commands one at a time on the command line, or it can
take batches of instructions in files called "playbooks". I'll discuss
playbooks later.

## Hello, World

This is the "Hello, World" command for Ansible.

    ansible all -a "echo Hello, World"

This will SSH into all the target machines in the inventory file and
make them send back "Hello, World". If any machines are not reachable
you'll see warnings about that. This is equivalent to typing:

    ssh <user>@<host> echo Hello, World

for every machine in the inventory file, but it's a lot less typing.

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

## Host and group variables

Ansible uses Jinja2-style templating for variables in commands. Our inventory
file defines some database-related variables for the "dev" group which are used
here.

    ansible db -m shell -a "echo 'show databases;' | mysql -h {{db_host}} -u {{db_user}} --password={{db_passwd}}"

There are also variables for individual hosts or machines. Each machine has an
`ansible_ssh_user` variable which Ansbile uses to put together SSH commands. The
workers all have `workdir` and `tasks` variables. These can be used with the same
kind of templating.

## Ansible modules

The `-m shell` argument above means that instead of running commands as we've normally
done, we are sending everything in double quotes to a shell command line, which
allows us to use the Unix pipe in the middle of the command. This uses the `shell`
module. Ansible has lots of modules, many of them user-contributed,
[listed by category](https://docs.ansible.com/ansible/latest/modules/modules_by_category.html),
and a
[flattened list](https://docs.ansible.com/ansible/latest/modules/list_of_all_modules.html).

The `-a "foo=this bar=that xyzzy=other"` piece is how arguments are passed to the module,
and this is actually taken from the INI syntax mentioned earlier. In playbooks, these
arguments are usually done as YAML lists.

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

## Finally, playbooks already

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
