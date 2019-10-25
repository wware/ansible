FROM ubuntu
Maintainer Will

RUN apt-get update
RUN apt-get install -y python python-pip wget openssh-server
RUN pip install Flask

RUN mkdir /var/run/sshd
RUN echo 'root:root' | chpasswd
RUN sed -i 's/PermitRootLogin .*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN ssh-keygen -P '' -f /root/.ssh/id_rsa -t rsa
RUN echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDRxOxfeAiJyNqNpnShmymyL0X/3FMlLRHynMcW48fsIbVYt4aVQbGWxT99ymwJJMVqHCdR6oBoyZWRIYmxi6BOLK2QdtfUq28Ya/1rqKpL+zYoCepPNVDE9qzvScslbBP298gqBMozu4zW1XlH1viyqhPkQ5BUEKG4VJW3BWykW7bWtjdARPokj9THzS+25IRMYv8/vwKtQ0b1/65YSEapXdGxA6YIOTuDKsWMoUoyBZgWaIqoUWVZYYilZqOJsNxufcyFOkGyIsNa/Gzd6BPo+AcT7vKdbA0gA9dGOKIOr4aWV6A09ifnSgKr9YoTE2rHPREJg2YO0JyH0kP7wFGR wware@wware-desktop64' > /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys

ADD hello.py /home/hello.py

WORKDIR /home
# ENTRYPOINT service ssh start && python /home/hello.py
# ENTRYPOINT service ssh start && bash
CMD service ssh start && python /home/hello.py
