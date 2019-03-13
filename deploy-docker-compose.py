#! /home/ebs/anaconda3/envs/ebs/bin/python3.6
# -*- coding:utf-8 -*-
# conda create --name ebs python=3.6
# pip install Crypto
# pip install pycrypto
# pip install paramiko
#
# To activate this environment, use:
# > source activate ebs
#
# To deactivate an active environment, use:
# > source deactivate
#
import sys
import os
import subprocess
import paramiko
from sys import argv
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
"""
ssh.connect(ip, port, username, password)
sftp = ssh.open_sftp()
"""

"""
workspaceDir为jenkins工作空间目录
"""
workspaceDir = "/home/ebs/.jenkins/workspace/"
"""
msDir为自定义目录
对应微服务的docker-compose.yml文件需放置在对应服务器的此目录
"""
msDir = "/data/ebs-ms/"
"""
msVersion版本号
"""
msVersion = "5.2.0-dhq-SNAPSHOT"
"""
ip为基础微服务所在服务器的ip
username/password为业务微服务所在服务器的普通账号/密码
port为业务微服务所在服务器的ssh端口
"""
serverInfo = {'ebsMs1': {'server': {'ip': '192.168.110.84', 'username': 'ebs', 'password': 'Yzb110#84.2018', 'port': '22'}, 'ebsMs': ['monitor', 'hystrix', 'sleuth', 'config', 'register', 'gateway', 'fbssw', 'system', 'member', 'biz', 'opening', 'fee', 'general', 'workflow2', 'message']}}

#和jenkins同一台服务器上的微服务
#jenkinsLocalMs = {'192.168.110.84': ['monitor', 'hystrix', 'sleuth', 'config', 'register', 'gateway', 'fbssw', 'system', 'member', 'biz', 'opening', 'fee', 'general', 'workflow2', 'message']}
jenkinsLocalMs={}

#jenkins的job分组
groupInfo = {'biz': 'dhq_purchase', 'opening': 'dhq_purchase', 'fee': 'dhq_purchase', 'general': 'dhq_purchase', 'system': 'dhq_base', 'member': 'dhq_base', 'workflow2': 'dhq_base', 'message': 'dhq_base', 'monitor': 'dhq_spc', 'hystrix': 'dhq_spc', 'sleuth': 'dhq_spc', 'config': 'dhq_spc', 'fbssw': 'dhq_spc', 'register': 'dhq_register', 'gateway': 'dhq_spcdev_gateway'}

#微服务别名
aliasInfo = {'monitor': 'dhq-monitor', 'hystrix': 'dhq-hystrix', 'sleuth': 'dhq-sleuth', 'config': 'dhq-config', 'register': 'dhq-register', 'gateway': 'dhq-gateway', 'fbssw': 'dhq-fbssw', 'system': 'dhq-system', 'member': 'dhq-member', 'biz': 'dhq-biz', 'opening': 'dhq-opening', 'fee': 'dhq-fee', 'general': 'dhq-general', 'workflow2': 'dhq-workflow2', 'message': 'dhq-message'}

#部署类型，docker/jar
deployType = 'docker'

# 构建后文件路径不一样
baseMs = ['monitor', 'hystrix', 'sleuth', 'config', 'register', 'gateway']
businessMs = ['fbssw', 'system', 'member', 'biz', 'opening', 'fee', 'general', 'workflow2', 'message']

# 每个模块包含哪些服务，构建用
base=['member', 'message', 'system', 'workflow2']
purchase=['biz', 'general', 'fee', 'opening']
spc=['register', 'config', 'monitor', 'hystrix', 'sleuth', 'fbssw']
business=['biz', 'general', 'fee', 'opening', 'member', 'system', 'workflow2', 'gateway', 'message']


def copyLoacl(ms):
    """
    复制本地微服务
    :param ms: 微服务名字
    """
    print("复制微服务" + ms)
    if ms in baseMs:
        msJenkinsTargetDir = workspaceDir + groupInfo[
            ms] + "ebs-" + ms + "-service/ebs-" + ms + "-service/target/"
    if ms in businessMs:
        msJenkinsTargetDir = workspaceDir + groupInfo[
            ms] + "ebs-" + ms + "-service/ebs-" + ms + "-service/" + ms + "-web/target/"


    if not os.path.exists(msJenkinsTargetDir):
        print('makelocaldir ' + msJenkinsTargetDir)
        os.makedirs(msJenkinsTargetDir)

        if ms in baseMs:
            subprocess.check_call("cp " + "-r " +
                             workspaceDir + "ebs-all-service/ebs-" + ms + "-service/target/ebs-" + ms + "-service-" + msVersion + ".jar " +
                             msJenkinsTargetDir + "ebs-" + ms + "-service-" + msVersion + ".jar",shell=True)

        if ms in businessMs:
            subprocess.check_call("cp ", "-r " +
                             workspaceDir + "ebs-all-service/ebs-" + ms + "-service/" + ms + "-web/target/" + ms + "-web-" + msVersion + ".jar " +
                             msJenkinsTargetDir + ms + "-web-" + msVersion + ".jar",shell=True)


def deployRemote(ms, ip, port, username, password):
    """
    发布远程微服务
    :param ms: 微服务名字
    """
    print("发布远程" + ms)
    msRemoteDir = msDir + "ebs-" + ms + "-service/"
    ssh.connect(ip, port, username, password)
    stdin, stdout, stderr = ssh.exec_command('ls ' + msRemoteDir)
    if stdout.readline() == '':
        stdin, stdout, stderr = ssh.exec_command("mkdir -p " + msRemoteDir)
    ssh.close()
    ssh.connect(ip, port, username, password)
    sftp = ssh.open_sftp()
    if ms in baseMs:
        msJenkinsDir = workspaceDir + groupInfo[
            ms] + "/ebs-" + ms + "-service/target/ebs-" + ms + "-service-" + msVersion + ".jar";
        sftp.put(
            msJenkinsDir,
            msRemoteDir + "app.jar")
    elif ms in businessMs:
        msJenkinsDir = workspaceDir + groupInfo[
            ms] + "/ebs-" + ms + "-service/" + ms + "-web/target/" + ms + "-web-" + msVersion + ".jar"
        sftp.put(
            msJenkinsDir,
            msRemoteDir + "app.jar")
    ssh.close()

def restartRemoteDocker(ms, ip, port, username, password):
    """
    重启远程微服务（docker方式）
    :param ms: 微服务名字
    """
    print("重启远程" + ms)
    ssh.connect(ip, port, username, password)
    dockerComposeCmd = "docker-compose -f " + msDir + "docker-compose.yml"
    dockerComposeUpCmd = dockerComposeCmd + " up -d " + aliasInfo[ms]
    dockerComposeRestartCmd = dockerComposeCmd + " restart " + aliasInfo[ms]
    stdin, stdout, stderr = ssh.exec_command(dockerComposeUpCmd)
    for item in stdout.readlines():
        print(item)
    stdin, stdout, stderr = ssh.exec_command(dockerComposeRestartCmd)
    for item in stdout.readlines():
        print(item)
    ssh.close()


def restartRemoteJar(ms, ip, port, username, password):
    """
    重启远程微服务（Jar包方式）
    :param ms: 微服务名字
    """
    print("重启远程" + ms)
    ssh.connect(ip, port, username, password)
    scriptPathFile = msDir + "ebs-" + ms + "-service/start.sh"
    scriptCmd = scriptPathFile + " restart "
    stdin, stdout, stderr = ssh.exec_command(scriptCmd)
    for item in stdout.readlines():
        print(item)
    ssh.close()


def deployLocal(ms, ip, port, username, password):
    """
    发布本地微服务
    :param ms: 微服务名字
    """
    print("发布本地" + ms)
    msLocalDir = msDir + "ebs-" + ms + "-service/"
    if not os.path.exists(msLocalDir):
        print('makelocaldir ' + msLocalDir)
        os.makedirs(msLocalDir)

    if ms in baseMs:
        msJenkinsDir = workspaceDir + groupInfo[
            ms] + "/ebs-" + ms + "-service/target/ebs-" + ms + "-service-" + msVersion + ".jar"
        subprocess.check_call("cp " + msJenkinsDir + " "+ msLocalDir + "app.jar",shell=True)
    elif ms in businessMs:
        msJenkinsDir = workspaceDir + groupInfo[
            ms] + "/ebs-" + ms + "-service/" + ms + "-web/target/" + ms + "-web-" + msVersion + ".jar"
        subprocess.check_call("cp " + msJenkinsDir + " " + msLocalDir + "app.jar",shell=True)


def restartLocalDocker(ms, ip, port, username, password):
    """
    重启本地微服务（docker方式）
    :param ms: 微服务名字
    """
    print("重启本地" + ms)
    dockerComposeCmd = "docker-compose -f " + msDir + "docker-compose.yml"
    dockerComposeUpCmd = dockerComposeCmd + " up -d " + aliasInfo[ms]
    dockerComposeRestartCmd = dockerComposeCmd + " restart " + aliasInfo[ms]
    subprocess.check_call(dockerComposeUpCmd,shell=True)
    subprocess.check_call(dockerComposeRestartCmd,shell=True)


def restartLocalJar(ms, ip, port, username, password):
    """
    重启本地微服务（jar包方式）
    :param ms: 微服务名字
    """
    print("重启远程" + ms)
    scriptPathFile = msDir + "ebs-" + ms + "-service/start.sh"
    scriptCmd = scriptPathFile + " restart "
    subprocess.check_call(scriptCmd,shell=True)


def deployAndRestart(ebsMs):
    """
    发布微服务
    :param ebsMs: 微服务列表
    """
    for ms in ebsMs:
        for key in serverInfo.keys():
            ebsMsi = serverInfo[key]['ebsMs']
            ipi = serverInfo[key]['server']['ip']
            porti = serverInfo[key]['server']['port']
            usernamei = serverInfo[key]['server']['username']
            passwordi = serverInfo[key]['server']['password']
            if ms in ebsMsi:
                print("发布重启" + ipi + "服务器的" + ms + "服务")
                deployAndRestartMs(ms, ipi, porti, usernamei, passwordi)


def deployAndRestartMs(ms, ip, port, username, password):
    if ip in jenkinsLocalMs.keys() and ms in jenkinsLocalMs[ip]:
        deployLocal(ms, ip, port, username, password)
        if deployType == "docker":
            restartLocalDocker(ms, ip, port, username, password)
        else:
            restartLocalJar(ms, ip, port, username, password)

    else:
        deployRemote(ms, ip, port, username, password)
        if deployType == "docker":
            restartRemoteDocker(ms, ip, port, username, password)
        else:
            restartRemoteJar(ms, ip, port, username, password)

start = time.time()
if len(argv) > 1:
    script, arg = argv
    if arg == 'base':
        deployAndRestart(base)
    elif arg == 'purchase':
        deployAndRestart(purchase)
    elif arg == 'spc':
        deployAndRestart(spc)
    elif arg == 'business':
        deployAndRestart(business)
    else:
        for key in serverInfo.keys():
            ebsMsi = serverInfo[key]['ebsMs']
            ipi = serverInfo[key]['server']['ip']
            porti = serverInfo[key]['server']['port']
            usernamei = serverInfo[key]['server']['username']
            passwordi = serverInfo[key]['server']['password']
            if arg in ebsMsi:
                print("发布重启" + ipi + "服务器")
                deployAndRestartMs(arg, ipi, porti, usernamei, passwordi)

else:
    print("请指定要发布的服务组：['base', 'purchase', 'spc', 'business']或者具体某个微服务['monitor', 'hystrix', 'sleuth', 'config', 'register', 'gateway', 'fbssw', 'system', 'member', 'biz', 'opening', 'fee', 'general', 'workflow2', 'message']！")
end = time.time()

print("耗时：", end - start)
