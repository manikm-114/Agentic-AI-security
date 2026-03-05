from src.history.verilog import VeriLog

def test_chain_ok():
    log = VeriLog()
    log.append(
        action="A", tool="t", args={}, result={},
        decision={"allowed": True},
        permissions_snapshot={"name": "x", "rules": {}},
        env_hash="abc"
    )
    assert log.verify_chain()
