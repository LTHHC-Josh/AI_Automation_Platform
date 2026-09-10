"""Explicit owned Windows scheduled activation. No registration occurs on import."""
from datetime import datetime,timezone,timedelta
from pathlib import Path
import getpass
import subprocess
import xml.etree.ElementTree as ET

TASK_NAME='LTHHC-ProgramCompliance'
DESCRIPTION='LTHHC Program Compliance owned schedule v1'
NS='http://schemas.microsoft.com/windows/2004/02/mit/task'


def schedule_xml(root,enabled=False):
    ET.register_namespace('',NS)
    task=ET.Element('{'+NS+'}Task',version='1.2')
    def child(parent,name,text=None,**attrs):
        node=ET.SubElement(parent,'{'+NS+'}'+name,attrs)
        if text is not None: node.text=text
        return node
    registration=child(task,'RegistrationInfo');child(registration,'Description',DESCRIPTION)
    triggers=child(task,'Triggers');trigger=child(triggers,'TimeTrigger')
    repetition=child(trigger,'Repetition');child(repetition,'Interval','PT15M');child(repetition,'StopAtDurationEnd','false')
    current=datetime.now(timezone.utc)
    boundary=current.replace(minute=(current.minute//15)*15,second=0,microsecond=0)+timedelta(minutes=15)
    child(trigger,'StartBoundary',boundary.isoformat(timespec='seconds'))
    child(trigger,'Enabled','true')
    principal=child(child(task,'Principals'),'Principal',id='Author')
    child(principal,'UserId',getpass.getuser());child(principal,'LogonType','InteractiveToken');child(principal,'RunLevel','LeastPrivilege')
    settings=child(task,'Settings')
    for key,value in {'MultipleInstancesPolicy':'IgnoreNew','DisallowStartIfOnBatteries':'false','StopIfGoingOnBatteries':'false','StartWhenAvailable':'true','Enabled':str(enabled).lower(),'Hidden':'true','ExecutionTimeLimit':'PT90M'}.items(): child(settings,key,value)
    execution=child(child(task,'Actions',Context='Author'),'Exec')
    child(execution,'Command',str(Path(root)/'.venv/Scripts/pythonw.exe'))
    child(execution,'Arguments','-m src.program_compliance tick');child(execution,'WorkingDirectory',str(root))
    return ET.tostring(task,encoding='unicode')


def install_schedule(root,directory,enabled):
    if not (Path(root)/'.venv/Scripts/pythonw.exe').is_file():
        raise RuntimeError('hidden_python_runtime_unavailable')
    query=subprocess.run(['schtasks.exe','/Query','/TN',TASK_NAME,'/XML'],capture_output=True)
    exists=query.returncode==0
    if exists:
        try:
            old=ET.fromstring(query.stdout.decode('utf-16') if query.stdout.startswith(b'\xff\xfe') else query.stdout.decode('utf-8-sig'))
            get=lambda name: old.find('.//{'+NS+'}'+name)
            if get('Description') is None or get('Description').text!=DESCRIPTION or get('Arguments').text!='-m src.program_compliance tick' or Path(get('Command').text) not in (Path(root)/'.venv/Scripts/python.exe',Path(root)/'.venv/Scripts/pythonw.exe'): raise ValueError()
        except Exception: raise RuntimeError('scheduled_task_ownership_unproven') from None
    elif not enabled:
        return
    path=Path(directory)/'schedule.xml';path.write_text(schedule_xml(root,enabled),encoding='utf-16')
    result=subprocess.run(['schtasks.exe','/Create','/TN',TASK_NAME,'/XML',str(path)]+(['/F'] if exists else []),capture_output=True)
    if result.returncode: raise RuntimeError('scheduled_task_registration_failed')
