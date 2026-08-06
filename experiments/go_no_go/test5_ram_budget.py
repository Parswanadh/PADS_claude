"""
GO/NO-GO TEST #5 -- RAM budget check.

This script itself is hardware-agnostic and runs correctly in any environment
(verified in the sandbox). The NUMBERS it reports here are this container's,
not the Latitude 5490's -- rerun it on the actual laptop, with the real
pipeline processes running, before trusting the result.

KILL SIGNAL: peak RSS across model(s) + classifier + turn-taking predictor +
OS overhead exceeds ~16 GB with insufficient headroom -> shrink model size
before adding engineering complexity (disk offloading, layer splitting).
"""
import psutil
import sys


TARGET_TOTAL_RAM_GB = 16.0
SAFETY_HEADROOM_GB = 3.0  # reserve for OS + other foreground apps, per the
                          # RAM-pressure discussion in the Detailed Report Sec 5.3


def current_process_tree_rss_gb(pids=None):
    """Sum RSS (in GB) across the given PIDs (or the current process if None).
    On the real hardware, pass the PIDs of: llama.cpp inference process,
    dialogue-act classifier process, turn-taking predictor process."""
    if pids is None:
        pids = [psutil.Process().pid]
    total_bytes = 0
    for pid in pids:
        try:
            total_bytes += psutil.Process(pid).memory_info().rss
        except psutil.NoSuchProcess:
            continue
    return total_bytes / (1024 ** 3)


def report():
    vm = psutil.virtual_memory()
    total_gb = vm.total / (1024 ** 3)
    available_gb = vm.available / (1024 ** 3)
    used_by_pipeline_gb = current_process_tree_rss_gb()

    print(f"System total RAM:      {total_gb:.2f} GB  (container figure -- rerun on Latitude 5490)")
    print(f"Currently available:   {available_gb:.2f} GB")
    print(f"This process's RSS:    {used_by_pipeline_gb:.3f} GB")
    print(f"Target budget:         {TARGET_TOTAL_RAM_GB:.1f} GB total, "
          f"{SAFETY_HEADROOM_GB:.1f} GB reserved headroom")
    print(f"Usable for the pipeline: {TARGET_TOTAL_RAM_GB - SAFETY_HEADROOM_GB:.1f} GB")

    budget_ok = (TARGET_TOTAL_RAM_GB - SAFETY_HEADROOM_GB) > 0
    if not budget_ok:
        print("\nKILL SIGNAL: no budget headroom at all under the stated target.")
        return False

    print("\nOn the real hardware: sum RSS across the llama.cpp inference process,")
    print("the dialogue-act classifier process, and the turn-taking predictor")
    print("process (see current_process_tree_rss_gb(pids=[...])), and compare")
    print(f"against the usable budget above ({TARGET_TOTAL_RAM_GB - SAFETY_HEADROOM_GB:.1f} GB).")
    print("If it doesn't fit: shrink model size FIRST, before adding disk")
    print("offloading or other engineering complexity.")
    return True


if __name__ == "__main__":
    ok = report()
    sys.exit(0 if ok else 1)
