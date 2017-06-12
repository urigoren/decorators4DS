import paramiko
import time
import os
import inspect
import pickle
import pandas as pd
import numpy as np

class ssh_connect:
    """This class wraps the clpd ssh access"""
    def __init__(self,user,password,server):
        """tests the connection"""
        self.user=user
        self.server=server
        self.password=password
        #initiate connection
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(self.server, username=self.user,password=self.password)
        self.chan=self.ssh_client.invoke_shell()
        self.stdout=self.exec_cmd("PS1='python-ssh:'")#ignore welcome message
        self.stdin=''
        self.keep_python=False
        self.in_process=''
        self.format={}
        self.python_cmd='python'

    def __del__(self):
        """close the ssh connection"""
        try:
            self.ssh_client.close()
            if os.path.isfile('py_ssh_tmp.sh'):
                os.remove('py_ssh_tmp.sh')
        except:
            pass

    def __call__(self, func):
        """convinience for self.py"""
        return self.py(func)

    def __rshift__(self, cmd):
        """convinience for self.exec_cmd"""
        self.exec_cmd(cmd, True)

    def exec_cmd(self,cmd,verbose=False):
        """Gets ssh command(s), execute them, and returns the output"""
        buff=''
        if type(cmd)!=list:
            cmd=[cmd]
        for c in cmd:
            self.chan.send(str(c)+'\n')
        while not self.chan.recv_ready():
            time.sleep(1)
        while not buff.endswith('python-ssh:'):
            r=self.chan.recv(1024)
            if (verbose):
                print (r.decode("utf-8"))
            buff+=r.decode("utf-8")
            #Auto insert password
            if buff.split('\n')[-1].strip().lower()=='password:':
                self.chan.send(self.password+'\n')
                time.sleep(100)
        return buff[:-11]

    def exec_code(self,python_code):
        """runs python code snippets on the ssh server and returns the raw response"""
        if self.keep_python:
            if self.in_process=='':
                self.stdin='\n'
            else:
                #start python process
                self.in_process='python'
                self.stdin='\n'+self.python_cmd+'\n'
        else:
            self.stdin='\n'+self.python_cmd+'\n'
        self.stdin+="import cPickle as pickle\n"
        self.stdin+="import subprocess\n"
        self.stdin+="def bash(cmd):\n\tret=subprocess.call(cmd+' >/dev/null 2>&1',shell=True)\n\treturn ret\n\n"
        self.stdin+="\nprint( '<RE'+'M'+'OTE>')\n"
        self.stdin+=python_code
        self.stdin+="\nprint( '</RE'+'M'+'OTE>')\n"
        if not self.keep_python:
            self.stdin+="exit()\n"
        self.stdout=self.exec_cmd(self.stdin)
        ret=self.stdout[self.stdout.find('<REMOTE>')+len('<REMOTE>'):self.stdout.find('</REMOTE>')]
        while ret.find('<IGNORE>')>-1:
            ret=ret[:ret.find('<IGNORE>')]+ret[ret.find('</IGNORE>')+9:]
        #ret=[l for l in ret.split('\r\n') if not (l.startswith('>>> ') or l.startswith('... '))]
        ret=[l for l in ret.split('\r\n') if not (l.startswith('>>> ') or l.startswith('... ') or (l.find(' INFO ')>-1) )]
        return ret[1:-1]

    def ctrl(self,letter):
        """simulate hitting ctrl+?"""
        ascii=ord(letter[0].upper())
        c=chr(ascii-64)
        self.chan.send(c)

    def env_var(self,varname):
        """Returns environment variable"""
        varval=self.exec_cmd("echo '<v''r>'$"+str(varname)+"'</v''r>'", False)
        varval=varval[varval.find('<vr>')+4:varval.find('</vr>')]
        return varval

    def bash(self,func):
        """Run bash commands"""
        cmd=func.__doc__
        if len(self.format)>0:
            cmd=cmd.format(**(self.format))
        with open('py_ssh_tmp.sh','w') as f:
            f.write(cmd)
        self.put_file('py_ssh_tmp.sh')
        time.sleep(3)
        ret=self.exec_cmd('. py_ssh_tmp.sh',True)
        self.stdout=ret
        self.stdin=cmd
        return lambda: '\n'.join([s.strip() for s in ret.split('\n')[1:]])

    def py(self,func):
        """Runs a python function in a remote ssh"""
        code_lines=inspect.getsourcelines(func)[0]
        code_lines=[l for l in code_lines if not (l.lstrip().startswith('@') or l.find('print ')>-1)]
        #remove indentation
        indent=0
        while ((indent*' ')+code_lines[0].lstrip()!=code_lines[0]):
            indent+=1
        code_lines=[l[indent:] for l in code_lines]
        signature= inspect.signature(func)
        #print the result
        def ret_func(*args, **kwargs):
            code_lines[0]='def {f}({args}):\n'.format(f=func.__name__,args=','.join([str(k) for k in signature.bind(*args, **kwargs).arguments.keys()]))
            python_code=''.join(code_lines)
            python_code+='\nret={f}({args})\n'.format(f=func.__name__,args=','.join([repr(k) for k in signature.bind(*args, **kwargs).arguments.values()]))
            python_code+='pickled=pickle.dumps(ret)\nprint ("<{t}>{p}</{t}>".format(p=repr(pickled),t="OU"+"TPUT" ))\n'
            #run on the server
            #print python_code
            pickled=self.exec_code(python_code)
            #print pickled
            pickled=pickled[0]
            pickled=pickled[pickled.find('<OUTPUT>')+len('<OUTPUT>'):pickled.find('</OUTPUT>')]
            pickled=eval(pickled)
            ret=pickle.loads(str.encode(pickled))
            return ret
        return ret_func

    def put_file(self,local_path,remote_path=None):
        """Copies a file to the server"""
        if (remote_path is None):
            remote_path=local_path
        sftp=self.ssh_client.open_sftp()
        sftp.put(local_path,remote_path)
        sftp.close()

    def get_file(self,remote_path,local_path=None):
        """Copies a file from the server"""
        if (local_path is None):
            local_path=remote_path
        sftp=self.ssh_client.open_sftp()
        sftp.get(remote_path,local_path)
        sftp.close()



if (__name__=='__main__'):
    ssh=ssh_connect('user','password','server')
    @ssh.py
    def python_pwd():
        import os
        return os.getcwd()
    print (python_pwd())

    @ssh.bash
    def ls():
        return "ls"
    print (ls())
