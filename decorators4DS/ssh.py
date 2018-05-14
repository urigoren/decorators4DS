import sys
import paramiko
import time
import os
import inspect
import pickle
import pandas as pd
from itertools import chain


class ssh_connect:
    """This class wraps the clpd ssh access
    @params:
        :server          - Required  : Server to connect (IP/Host)                                     (Str)
        :user            - Required  : Ssh user for connect                                            (Str)
        :password        - Optional  : Ssh pass for user. Default = ''                                 (Str)
        :port            - Optional  : Specific ssh port. Default = 22                                 (Int)
        :privateKeyFile  - Optional  : Path to your private ssh key file. Default = '~/.ssh/id_rsa'    (Str)
        :interpreter     - Optional  : Path to interpreter on remote host. Default = '/usr/bin/python' (Str)
        :verbose         - Optional  : Verbosity output                                                (Bool)
        ...
    @usage:
        ssh = ssh_connect('host', 'login', 'password', port=22,
                          privateKeyFile='~/.ssh/id_rsa', interpreter='/usr/bin/python',
                          verbose=True)

        @ssh
        def py_func(*args)
        ...

        print(py_func(args))
    """

    def __init__(self, server, user, password="", port=22,
                 privateKeyFile='~/.ssh/id_rsa', interpreter='/usr/bin/python',
                 verbose=False):
        """tests the connection"""
        self.user = user
        self.server = server
        self.password = password
        self.port = port
        self.verbose = verbose
        # initiate connection
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        privateKeyFile = privateKeyFile if os.path.isabs(privateKeyFile) else os.path.expanduser(privateKeyFile)
        if os.path.exists(privateKeyFile):
            private_key = paramiko.RSAKey.from_private_key_file(privateKeyFile)
            self.ssh_client.connect(server, port=port, username=user, pkey=private_key)
        else:
            self.ssh_client.connect(server, port=port, username=user, password=password)
        self.chan = self.ssh_client.invoke_shell()
        self.stdout = self.exec_cmd("PS1='python-ssh:'")  # ignore welcome message
        self.stdin = ''
        self.keep_python = False
        self.in_process = ''
        self.format = {}
        self.python_cmd = interpreter
        self.cast_dict_to_dataframe = True

    def __del__(self, command=None):
        """close the ssh connection"""
        try:
            if command:
                self.exec_cmd(command)
            if os.path.isfile('py_ssh_tmp.sh'):
                self.exec_cmd('rm py_ssh_tmp.sh')
                os.remove('py_ssh_tmp.sh')
            self.ssh_client.close()
        except Exception:
            pass

    def __call__(self, func):
        """convinience for self.py"""
        return self.py(func)

    def __rshift__(self, cmd):
        """convinience for self.exec_cmd"""
        self.exec_cmd(cmd)

    def close(self, command=None):
        self.__del__(command)

    def __cleanup__(self, func):
        """Clean up function.
        Remove: `doc-strings`, `comments`, `empty lines`, `decoraters`
        and `prints` if "verbose" key is False from input function"""

        def _cleanup_docstring_(line):
            triple_commons_cases = ('"""', "'''")
            _ = line.strip()
            if hasattr(_cleanup_docstring_, 'TRIGGER'):
                if _.endswith(triple_commons_cases[0]) or line.endswith(triple_commons_cases[1]):
                    delattr(_cleanup_docstring_, 'TRIGGER')
            elif _.startswith(triple_commons_cases[0]) or line.startswith(triple_commons_cases[1]):
                _cleanup_docstring_.TRIGGER = True
            else:
                return line

        code_lines = (_cleanup_docstring_(l) for l in inspect.getsourcelines(func)[0])
        if not self.verbose:
            code_lines = (x for x in code_lines if not [i for i in ('print(', 'print ') if i in x])
        clean_comments = (x.split('#')[0] for x in code_lines if x)
        clean_empty_lines = (x for x in clean_comments if x and not x.isspace())
        clean_deco = (x for x in clean_empty_lines if not x.lstrip().startswith('@'))
        return map(lambda x: x if x.endswith('\n') else ''.join((x,'\n')) ,clean_deco) # add new line to ich line

    @property
    def local_pyversion(self):
        """Version of local curent python"""
        if not hasattr(self, '_pyversion'):
            self._pyversyon = sys.version_info.major
        return self._pyversyon

    @property
    def remote_pyversion(self):
        """Trying to get remote python version"""
        if not hasattr(self, '_remote_py_version'):
            buf_str = self.exec_cmd('''%s -c "import sys;print('{v}'.format(v=sys.version_info[0]))"''' % self.python_cmd)
            self._remote_py_version = int(buf_str.split()[-1])
        return self._remote_py_version

    def exec_cmd(self, cmd):
        """Gets ssh command(s), execute them, and returns the output"""
        buff = ''
        if type(cmd) != list:
            cmd = [cmd]
        for c in cmd:
            self.chan.send(str(c) + '\n')
        while not self.chan.recv_ready():
            time.sleep(1)
        while not buff.endswith('python-ssh:'):
            r = self.chan.recv(1024)
            if self.verbose:
                print(r.decode("utf-8"))
            buff += r.decode("utf-8")
            # Auto insert password
            if self.password is not None and buff.split('\n')[-1].strip().lower() == 'password:':
                self.chan.send(self.password + '\n')
                time.sleep(100)
        return buff[:-11]

    def exec_code(self, python_code):
        """runs python code snippets on the ssh server and returns the raw response"""
        if self.keep_python:
            if self.in_process == '':
                self.stdin = '\n'
            else:
                # start python process
                self.in_process = 'python'
                self.stdin = '\n' + self.python_cmd + '\n'
        else:
            self.stdin = '\n' + self.python_cmd + '\n'
        self.stdin += "import pickle, json, collections, itertools, sys, os, subprocess, traceback\n"
        self.stdin += "try:\n\timport pandas as pd\nexcept ImportError:\n\tpass\n\n"
        self.stdin += "def bash(cmd):\n\tret=subprocess.call(cmd+' >/dev/null 2>&1',shell=True)\n\treturn ret\n\n"
        self.stdin += "\nprint( '<RE'+'M'+'OTE>')\n"
        self.stdin += python_code
        self.stdin += "\nprint( '</RE'+'M'+'OTE>')\n"
        if not self.keep_python:
            self.stdin += "exit()\n"
        self.stdout = self.exec_cmd(self.stdin)
        ret = self.stdout[self.stdout.find('<REMOTE>') + len('<REMOTE>'):self.stdout.find('</REMOTE>')]
        self.stdout = ''
        while ret.find('<IGNORE>') > -1:
            ret = ret[:ret.find('<IGNORE>')] + ret[ret.find('</IGNORE>') + 9:]
        # ret=[l for l in ret.split('\r\n') if not (l.startswith('>>> ') or l.startswith('... '))]
        ret = [l for l in ret.split('\r\n') if
               not (l.startswith('>>> ') or l.startswith('... ') or (l.find(' INFO ') > -1))]
        return ret[1:-1]

    def ctrl(self, letter):
        """simulate hitting ctrl+?"""
        ascii = ord(letter[0].upper())
        c = chr(ascii - 64)
        self.chan.send(c)

    def env_var(self, varname):
        """Returns environment variable"""
        varval = self.exec_cmd("echo '<v''r>'$" + str(varname) + "'</v''r>'")
        varval = varval[varval.find('<vr>') + 4:varval.find('</vr>')]
        return varval

    def bash(self, func):
        """Run bash commands"""
        cmd = func.__doc__
        if not any(func.__doc__):
            raise SyntaxError("docstring cannot be empty")
        if len(self.format) > 0:
            cmd = cmd.format(**self.format)
        with open('py_ssh_tmp.sh', 'w') as f:
            f.write(cmd)
        self.put_file('py_ssh_tmp.sh')
        time.sleep(3)
        ret = self.exec_cmd('. py_ssh_tmp.sh')
        self.stdout = ret
        self.stdin = cmd
        return lambda: '\n'.join([s.strip() for s in ret.split('\n')[1:]])

    def py(self, func):
        """Runs a python function in a remote ssh"""
        code_lines = self.__cleanup__(func)
        first_line = next(code_lines)
        # remove indentation
        indent = 0
        while (indent * ' ') + first_line.lstrip() != first_line:
            indent += 1
        code_lines = (l[indent:] for l in code_lines)
        if self.local_pyversion is 3:
            signature = inspect.signature(func)
        else:
            signature = inspect.getargspec(func)

        def ret_func(*args, **kwargs):
            first_line = 'def {f}({args}):\n'
            last_line = 'try:\n\tret=("",{f}({args}))\n' \
                        'except Exception:\n\tret=(traceback.format_exc(), None)\n\n'

            if self.local_pyversion == 3:
                first_line = first_line.format(f=func.__name__, args=','.join(
                    (str(k) for k in signature.bind(*args, **kwargs).arguments.keys())))
                last_line = last_line.format(f=func.__name__, args=','.join(
                    (repr(k) for k in signature.bind(*args, **kwargs).arguments.values())))
            else:
                first_line = first_line.format(f=func.__name__, args=','.join((str(k) for k in signature.args)))
                kw = dict(zip(signature.args, args) + kwargs.items())
                last_line = last_line.format(f=func.__name__, args=','.join(
                    (str(k) + "=" + repr(v) for k, v in kw.items())))
            pandas_code = 'if "pd" in globals() and isinstance(ret, pd.DataFrame):\n\tret=ret.to_dict()\n\n'
            pickled_code = 'pickled=pickle.dumps(ret)\nprint("<{t}>{p}</{t}>".format(p=repr(pickled),t="OU"+"TPUT" ))\n'
            python_code = ''.join(chain(first_line, code_lines, '\n', last_line, pandas_code, pickled_code))
            # print python_code
            # run on the server
            pickled = self.exec_code(python_code)
            # print pickled
            pickled = [i for i in pickled if '<OUTPUT>' in i][0]
            pickled = pickled[pickled.find('<OUTPUT>') + len('<OUTPUT>'):pickled.find('</OUTPUT>')]
            pickled = eval(pickled)
            if self.local_pyversion != self.remote_pyversion:
                err, ret = pickle.loads(str.encode(pickled))
            else:
                err, ret = pickle.loads(pickled)
            if any(err):
                raise SystemError(err)
            if isinstance(ret, dict) and self.cast_dict_to_dataframe:
                # if all the dictionary keys have the same number of records:
                if len(set([len(v) for k, v in ret.items()])) == 1:
                    ret = pd.DataFrame(ret)
            return ret

        return ret_func

    def put_file(self, local_path, remote_path=None):
        """Copies a file to the server"""
        if remote_path is None:
            remote_path = local_path
        sftp = self.ssh_client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()

    def get_file(self, remote_path, local_path=None):
        """Copies a file from the server"""
        if local_path is None:
            local_path = remote_path
        sftp = self.ssh_client.open_sftp()
        sftp.get(remote_path, local_path)
        sftp.close()


if __name__ == '__main__':
    ssh = ssh_connect('host', 'login', 'password', verbose=True)

    @ssh
    def python_pwd():
        import os
        return os.getcwd()


    print(python_pwd())


    @ssh.bash
    def ls():
        """ls"""
        return "ls"


    print(ls())
