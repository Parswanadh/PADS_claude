"""
GO/NO-GO TEST #2 helper -- extracts real between-speaker gap (pause)
durations from the AMI Meeting Corpus, as a verified freely-available
alternative to LDC-gated Switchboard/CallHome.

Source: AMI Meeting Corpus manual annotations v1.6.2,
https://groups.inf.ed.ac.uk/ami/download/ -- CC BY 4.0, no LDC gating,
no registration wall, downloaded and verified directly (HTTP 200, no
auth) on 2026-08-08. Word-level start/end timestamps (seconds) are
present per participant per meeting in words/<meeting>.<participant>.words.xml.

IMPORTANT CAVEAT: AMI is 4-5 person, in-person, task-oriented business
meetings -- a different conversational register than Switchboard/
CallHome's dyadic telephone conversations. Do not present this as a
Switchboard-equivalent result; it is a real, verified, freely-available
DIFFERENT corpus, honestly labeled as such. It genuinely answers "what do
real between-speaker gap durations look like in real human conversation
recordings," which is what Go/No-Go Test 2 actually needs, just not from
the originally-planned specific corpus.

Method: merge every participant's word-level (start, end) timestamps in
a meeting into one chronological sequence. Whenever consecutive entries
in that sequence belong to different speakers and the later one starts
after the earlier one ends (no overlap), record the gap
(next.start - prev.end) as a between-speaker pause. This mirrors
Heldner & Edlund (2010)'s operational definition of a "gap" (a
between-speaker silence at a floor transfer), computed directly from
word-level VAD-equivalent timestamps rather than continuous voice-activity
detection.

Usage:
    python test2_extract_ami_pause_durations.py \
        --words-dir /path/to/extracted/words \
        --output experiments/results/test2_ami_pause_durations.json
"""
import argparse
import glob
import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict


def load_words(path):
    tree = ET.parse(path)
    root = tree.getroot()
    words = []
    for w in root.findall("{http://nite.sourceforge.net/}w") + root.findall("w"):
        start = w.get("starttime")
        end = w.get("endtime")
        if start is None or end is None:
            continue
        words.append((float(start), float(end)))
    return words


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--words-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    by_meeting = defaultdict(list)  # meeting_id -> list of (start, end, speaker)
    files = sorted(glob.glob(os.path.join(args.words_dir, "*.words.xml")))
    for path in files:
        base = os.path.basename(path)
        parts = base.split(".")
        if len(parts) < 4:
            continue
        meeting_id, speaker = parts[0], parts[1]
        for start, end in load_words(path):
            by_meeting[meeting_id].append((start, end, speaker))

    gaps = []
    for meeting_id, entries in by_meeting.items():
        entries.sort(key=lambda e: e[0])
        for i in range(1, len(entries)):
            prev_start, prev_end, prev_speaker = entries[i - 1]
            cur_start, cur_end, cur_speaker = entries[i]
            if cur_speaker == prev_speaker:
                continue
            gap = cur_start - prev_end
            if gap > 0:
                gaps.append(gap)

    gaps.sort()
    n = len(gaps)
    print(f"Meetings processed: {len(by_meeting)}")
    print(f"Real between-speaker gaps extracted: {n}")
    if n:
        print(f"min={gaps[0]*1000:.1f}ms max={gaps[-1]*1000:.1f}ms")
        print(f"median={gaps[n // 2]*1000:.1f}ms mean={sum(gaps) / n * 1000:.1f}ms")
        print(f"p25={gaps[n // 4]*1000:.1f}ms p75={gaps[3 * n // 4]*1000:.1f}ms")

    with open(args.output, "w") as f:
        json.dump(gaps, f)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
