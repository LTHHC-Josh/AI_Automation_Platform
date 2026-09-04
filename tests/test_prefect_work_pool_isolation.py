from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "prefect.yaml"
CONTROL = ROOT / "scripts" / "invoke_prefect_control_room.ps1"
LIVE = ROOT / "scripts" / "invoke_prefect_document_processor.ps1"
MANUAL = ROOT / "scripts" / "invoke_prefect_mailbox_worker.ps1"
TRAINING = ROOT / "scripts" / "invoke_prefect_document_processor_training.ps1"


def read(path):
    return path.read_text(encoding="utf-8-sig")


def test_deployments_route_to_three_exact_service_pools():
    deployments = {
        item["name"]: item
        for item in yaml.safe_load(read(CONFIG))["deployments"]
    }
    expected = {
        "document-processor-live": "lthhc-dp-live-process",
        "document-processor-manual": "lthhc-local-process",
        "document-processor-training": "lthhc-dp-training-process",
    }
    for name, pool in expected.items():
        deployment = deployments[name]
        assert deployment["work_pool"]["name"] == pool
        assert deployment["work_pool"]["job_variables"] == {}
        assert deployment["parameters"] == {}
        assert deployment["schedule"] is None
        assert deployment["concurrency_limit"] == {
            "limit": 1,
            "collision_strategy": "CANCEL_NEW",
        }
    assert deployments["document-processor-live"]["entrypoint"].endswith(
        ":unattended_mailbox_flow"
    )
    assert deployments["document-processor-manual"]["entrypoint"].endswith(
        ":bounded_mailbox_flow"
    )
    assert deployments["document-processor-training"]["entrypoint"].endswith(
        ":document_processor_training_flow"
    )


def test_worker_launchers_are_pool_specific_and_non_overlapping():
    live = read(LIVE)
    manual = read(MANUAL)
    training = read(TRAINING)
    assert "lthhc-dp-live-process" in live
    assert "lthhc-dp-live-worker" in live
    assert "lthhc-local-process" not in live
    assert "lthhc-dp-training-process" not in live
    assert "lthhc-local-process" in manual
    assert "lthhc-local-worker" in manual
    assert "lthhc-dp-live-process" not in manual
    assert "lthhc-dp-training-process" not in manual
    assert "lthhc-dp-training-process" in training
    assert "lthhc-dp-training-worker" in training
    assert "lthhc-dp-live-process" not in training
    assert "lthhc-local-process" not in training
    for source in (live, manual, training):
        assert "--limit" in source
        assert "--no-create-pool-if-not-found" in source


def test_control_wrapper_uses_service_specific_pool_health_and_stop_boundaries():
    source = read(CONTROL)
    assert "$manualPoolName = 'lthhc-local-process'" in source
    assert "$livePoolName = 'lthhc-dp-live-process'" in source
    assert "$trainingPoolName = 'lthhc-dp-training-process'" in source

    live_start = source.split("function Start-DocumentProcessor {", 1)[1].split(
        "function Stop-DocumentProcessor", 1
    )[0]
    live_stop = source.split("function Stop-DocumentProcessor {", 1)[1].split(
        "function Start-DocumentProcessorTraining", 1
    )[0]
    manual_stop = source.split("function Stop-ControlRoomWorker {", 1)[1].split(
        "function Start-DocumentProcessor", 1
    )[0]
    training_stop = source.split(
        "function Stop-DocumentProcessorTraining {", 1
    )[1].split("function Stop-ControlRoomInfrastructure", 1)[0]

    assert "Get-FreshOnlineWorkerCount $livePoolName" in live_start
    assert "live_pool_ready" in live_start
    assert "Start-OwnedComponent -Name 'dp'" in live_start
    assert "Stop-OwnedComponent -Name 'dp'" in live_stop
    assert "live_fresh_online_worker_count" in live_stop
    assert "Stop-ControlRoomWorker" not in live_stop
    assert "Stop-OwnedComponent -Name 'worker'" in manual_stop
    assert "live_fresh_online_worker_count" not in manual_stop
    assert "Stop-OwnedComponent -Name 'dp'" not in manual_stop
    assert "Stop-OwnedComponent -Name 'dp_training'" in training_stop
    assert "Stop-OwnedComponent -Name 'dp'" not in training_stop


def test_manual_commands_never_route_or_stop_the_live_worker():
    source = read(CONTROL)
    prepare = source.split("'PrepareRun' {", 1)[1].split("'RunOnce' {", 1)[0]
    run_once = source.split("'RunOnce' {", 1)[1].split("'StopWorker' {", 1)[0]
    stop_worker = source.split("'StopWorker' {", 1)[1].split("'StartDP' {", 1)[0]
    assert "Start-OwnedComponent -Name 'worker'" in prepare
    assert "live_fresh_online_worker_count" in prepare
    assert "deployment run $deploymentName --watch" in run_once
    assert "live_fresh_online_worker_count" in run_once
    assert "Stop-ControlRoomWorker" in stop_worker
    assert "Stop-DocumentProcessor" not in stop_worker


def test_status_dp_names_only_the_live_pool_and_is_phi_safe():
    source = read(CONTROL)
    status = source.split("function Get-DocumentProcessorStatus {", 1)[1].split(
        "function Get-DocumentProcessorTrainingStatus", 1
    )[0]
    formatter = source.split(
        "function Write-DocumentProcessorOperatorStatus", 1
    )[1].split("function Write-StartupProgress", 1)[0]
    assert "work_pool_name = $livePoolName" in status
    assert "work_pool_ready = $control.live_pool_ready" in status
    assert "fresh_online_worker_count = $control.live_fresh_online_worker_count" in status
    assert "Write-OperatorField 'Work Pool' $Status.work_pool_name" in formatter
    for prohibited in (
        "message_id", "subject", "filename", "row_id", "source_text", "payload"
    ):
        assert prohibited not in (status + formatter).lower()


if __name__ == "__main__":
    tests = [
        value for name, value in tuple(globals().items())
        if name.startswith("test_")
    ]
    for test in tests:
        test()
    print(f"Passed: {len(tests)}")
    print("Failed: 0")
    print("Classification: synthetic deterministic/static Prefect routing")
    print("External integrations: not called")
    print("PHI handling: fixed pool, deployment, worker, and status names only")
