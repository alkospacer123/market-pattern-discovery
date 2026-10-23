"""Test-only process fault driver. Synthetic signals; exact production loop.

No CLI option in the trading loop enables these injection points. Parent tests
kill this interpreter with the OS, without calling close or unwinding SQLite.
"""
import argparse
import json
import os
import sys
from unittest.mock import patch

from .test_m15_runner import T, candle, signal
from .. import m15_runner as runner


def summary(bot, phase):
    return dict(phase=phase, pid=os.getpid(), robot=bot.robot_id,
                account=bot.broker.account_id, post_count=bot.broker.post_count,
                positions=bot.broker.snapshot()["positions"],
                halt=bot.store.get("execution_halt"),
                intents=len(bot.store.all_intents()), fills=len(bot.store.all_fills()),
                reservations=bot.store.get("risk_reservations", {}))


def emit(value):
    print(json.dumps(value), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    p.add_argument("--robot", default="v20-shallow")
    p.add_argument("--phase", choices=("signal", "intent", "post", "ack", "fill", "stop", "protected"))
    args = p.parse_args()
    try:
        with runner.M15OfflineRobot(args.root, args.robot) as bot:
            def pause(phase):
                if args.phase == phase:
                    emit(summary(bot, phase))
                    # Parent deliberately kills us while this pipe remains open.
                    sys.stdin.readline()
                    raise RuntimeError("FAULT_CHILD_MUST_BE_KILLED")

            original_transition = bot.store.transition_intent
            def transition(key, status, *a, **kw):
                if status == "SUBMITTED" and not key.endswith((":stop", ":exit")):
                    pause("intent")  # committed reserve/quota/intent, before POST
                return original_transition(key, status, *a, **kw)

            original_post = bot.broker.submit
            def post(wire, **kw):
                result = original_post(wire, **kw)
                pause("stop" if kw.get("kind") == "STOP" else "post")
                return result

            original_fill = bot.broker.fill
            def fill(*a, **kw):
                pause("ack")
                result = original_fill(*a, **kw)
                pause("fill")
                return result

            def frozen(*a, **kw):
                value = signal(*a, **kw)
                pause("signal")
                return value

            with patch.object(runner, "completed_signal", side_effect=frozen), \
                 patch.object(bot.store, "transition_intent", side_effect=transition), \
                 patch.object(bot.broker, "submit", side_effect=post), \
                 patch.object(bot.broker, "fill", side_effect=fill):
                boundary = dict(at="2024-01-09T10:15:00", updates={"CNYRUBF": dict(open="10", bars=[])})
                if args.phase:
                    bot.on_event(dict(at=boundary["at"], history={"CNYRUBF": [candle(T)]}))
                bot.on_event(boundary)  # duplicate on recovery, never replay late
                emit(summary(bot, "protected" if args.phase else "recovered"))
            for line in sys.stdin:
                if line.strip():
                    result = bot.on_event(json.loads(line))
                    emit(dict(summary(bot, "event"), result=result))
    except Exception as exc:
        emit(dict(phase="blocked", pid=os.getpid(), error=str(exc)))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
