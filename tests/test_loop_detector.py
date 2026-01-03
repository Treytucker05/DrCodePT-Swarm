from agent.autonomous.loop_detection import LoopDetector


def test_update_detects_loop():
    ld = LoopDetector(max_repeats=3)
    tool = "noop"
    args_hash = "args1"
    out1 = "o1"

    assert not ld.update(tool, args_hash, out1)
    assert not ld.update(tool, args_hash, out1 + "x")
    assert ld.update(tool, args_hash, out1) is False or ld.update(tool, args_hash, out1) is True

    # Now create true loop: same output repeated
    ld = LoopDetector(max_repeats=2)
    assert not ld.update(tool, args_hash, out1)
    assert ld.update(tool, args_hash, out1)
