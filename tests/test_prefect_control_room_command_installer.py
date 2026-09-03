from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "scripts" / "install_prefect_control_room_commands.ps1"
COMMANDS = {
    "startui": "StartUI",
    "status": "Status",
    "preparerun": "PrepareRun",
    "runonce": "RunOnce",
    "stopworker": "StopWorker",
    "startdp": "StartDP",
    "statusdp": "StatusDP",
    "stopdp": "StopDP",
    "startdptraining": "StartDPTraining",
    "statusdptraining": "StatusDPTraining",
    "stopdptraining": "StopDPTraining",
    "restartui": "RestartControlRoom",
    "stopui": "StopControlRoom",
}


def run_powershell(command, cwd):
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_installer_is_idempotent_preserves_profile_and_commands_work_outside_repo():
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        fake_root = temporary / "verified-root"
        scripts = fake_root / "scripts"
        scripts.mkdir(parents=True)
        wrapper = scripts / "invoke_prefect_control_room.ps1"
        wrapper.write_text("param([string]$Action) Write-Output $Action\n", encoding="utf-8")
        profile = temporary / "profile.ps1"
        profile.write_text("$global:ExistingProfileValue = 'preserved'\n", encoding="utf-8")
        install = (
            f"& '{INSTALLER}' -ProfilePath '{profile}' "
            f"-RepositoryRoot '{fake_root}' -SkipExecutionPolicyCheck"
        )
        first = run_powershell(install, temporary)
        assert first.returncode == 0, first.stderr
        first_text = profile.read_text(encoding="utf-8-sig")
        second = run_powershell(install, temporary)
        assert second.returncode == 0, second.stderr
        second_text = profile.read_text(encoding="utf-8-sig")
        assert first_text == second_text
        assert "$global:ExistingProfileValue = 'preserved'" in second_text
        assert second_text.count("BEGIN LTHHC PREFECT CONTROL ROOM COMMANDS") == 1
        assert second_text.count("END LTHHC PREFECT CONTROL ROOM COMMANDS") == 1

        invocations = "; ".join(f"{command}" for command in COMMANDS)
        verify = run_powershell(
            f". '{profile}'; if($global:ExistingProfileValue -ne 'preserved'){{exit 9}}; {invocations}",
            temporary,
        )
        assert verify.returncode == 0, verify.stderr
        assert verify.stdout.splitlines() == list(COMMANDS.values())


def test_profile_section_has_only_one_wrapper_invocation_per_command():
    source = INSTALLER.read_text(encoding="utf-8-sig")
    assert "CurrentUserAllHosts" in source
    assert "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned" in source
    assert "function global:" in source
    assert source.count("& '$escapedWrapperPath' -Action") == 1
    for command, action in COMMANDS.items():
        assert f"{command} = '{action}'" in source
    for prohibited in ("worker start", "deployment run", "Graph", "mailbox", "token", "payload"):
        assert prohibited not in source


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic isolated-profile")
    print("External integrations: not called")
    print("PHI handling: synthetic paths and action names only")
