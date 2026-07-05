"""Generate an offline, source-only human review page for Commons candidates."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path


def _text(value: object) -> str:
    return html.escape(str(value), quote=True)


def generate_review_page(manifest_path: str | Path, output_path: str | Path) -> int:
    manifest = Path(manifest_path)
    output = Path(output_path)
    payload = json.loads(manifest.read_text())
    cases = [
        case
        for case in payload.get("cases", [])
        if case.get("source") == "Wikimedia Commons"
    ]
    cards: list[str] = []
    for case in cases:
        image_path = manifest.parent / str(case["path"])
        relative_image = os.path.relpath(image_path, output.parent)
        labels = ", ".join(case.get("labels", [])) or "—"
        negatives = ", ".join(case.get("negative_for", [])) or "—"
        cards.append(
            f"""
            <article class="card" data-id="{_text(case['id'])}">
              <img loading="lazy" src="{_text(relative_image)}" alt="{_text(case['id'])}">
              <h2>{_text(case['id'])}</h2>
              <p><b>建议正例：</b>{_text(labels)}</p>
              <p><b>建议困难反例：</b>{_text(negatives)}</p>
              <p><a href="{_text(case.get('provenance_url', ''))}">{_text(case.get('source_title', 'source'))}</a></p>
              <p><b>许可：</b>{_text(case.get('license', ''))}　<b>当前：</b>{_text(case.get('review_status', ''))}</p>
              <label>决定
                <select class="decision">
                  <option value="">未决定</option>
                  <option value="accepted">接受</option>
                  <option value="rejected">拒绝</option>
                  <option value="ambiguous">歧义</option>
                  <option value="pending">退回待审</option>
                </select>
              </label>
              <label>说明<textarea class="notes" placeholder="必须基于画面和规格定义，不查看 CameraQ 输出"></textarea></label>
            </article>
            """
        )
    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>CameraQ 构图候选人工复核</title>
  <style>
    body {{ margin: 0; padding: 24px; color: #ececec; background: #111; font: 14px system-ui, sans-serif; }}
    header {{ position: sticky; top: 0; z-index: 2; padding: 14px; background: #181818ee; border: 1px solid #444; }}
    .warning {{ color: #ffd86b; }}
    main {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-top: 18px; }}
    .card {{ padding: 12px; background: #202020; border: 1px solid #3c3c3c; border-radius: 10px; }}
    .card.invalid {{ border-color: #ff5d5d; box-shadow: 0 0 0 2px #ff5d5d55; }}
    img {{ width: 100%; height: 210px; object-fit: contain; background: #080808; }}
    h2 {{ font-size: 13px; overflow-wrap: anywhere; }}
    label {{ display: block; margin-top: 10px; }}
    select, input, textarea, button {{ box-sizing: border-box; width: 100%; padding: 8px; color: #fff; background: #2c2c2c; border: 1px solid #666; }}
    textarea {{ min-height: 68px; resize: vertical; }}
    button {{ margin-top: 10px; background: #0b6; border: 0; font-weight: 700; cursor: pointer; }}
    a {{ color: #82cfff; }}
  </style>
</head>
<body>
  <header>
    <h1>构图候选人工复核（{len(cases)} 张）</h1>
    <p class="warning">必须独立判断，不得查看 CameraQ output／预测结果。来源类别仅用于提名，不是真值。</p>
    <p id="progress">已决定 0 / {len(cases)}</p>
    <label>复核者<input id="reviewer" placeholder="姓名或稳定复核者 ID"></label>
    <button id="download">导出 decisions.csv</button>
  </header>
  <main>{''.join(cards)}</main>
  <script>
    const csvEscape = value => '"' + String(value).replaceAll('"', '""') + '"';
    const storageKey = 'cameraq-composition-review-v1';
    const cards = Array.from(document.querySelectorAll('.card'));
    const reviewerInput = document.getElementById('reviewer');
    const loadState = () => {{
      try {{ return JSON.parse(localStorage.getItem(storageKey) || '{{}}'); }}
      catch (_) {{ return {{}}; }}
    }};
    const saveState = state => {{
      try {{ localStorage.setItem(storageKey, JSON.stringify(state)); }}
      catch (_) {{ /* file:// storage may be unavailable; exporting still works */ }}
    }};
    const state = loadState();
    reviewerInput.value = state.reviewer || '';
    const persist = () => {{
      const decisions = {{}};
      cards.forEach(card => {{
        const decision = card.querySelector('.decision').value;
        const notes = card.querySelector('.notes').value;
        if (decision || notes) decisions[card.dataset.id] = {{decision, notes}};
      }});
      saveState({{reviewer: reviewerInput.value, decisions}});
    }};
    const updateProgress = () => {{
      const decided = cards.filter(card => card.querySelector('.decision').value).length;
      document.getElementById('progress').textContent = `已决定 ${{decided}} / ${{cards.length}}`;
    }};
    cards.forEach(card => {{
      const saved = (state.decisions || {{}})[card.dataset.id] || {{}};
      card.querySelector('.decision').value = saved.decision || '';
      card.querySelector('.notes').value = saved.notes || '';
      card.querySelector('.decision').addEventListener('change', () => {{
        card.classList.remove('invalid'); persist(); updateProgress();
      }});
      card.querySelector('.notes').addEventListener('input', () => {{
        card.classList.remove('invalid'); persist();
      }});
    }});
    reviewerInput.addEventListener('input', persist);
    updateProgress();
    document.getElementById('download').addEventListener('click', () => {{
      const reviewer = reviewerInput.value.trim();
      if (!reviewer) {{ alert('请填写复核者'); return; }}
      // decision,reviewer,review_notes are the only mutable review fields.
      const decided = [];
      const invalid = [];
      cards.forEach(card => {{
        const decision = card.querySelector('.decision').value;
        if (!decision) return;
        const notes = card.querySelector('.notes').value.trim();
        if (decision !== 'pending' && !notes) {{
          card.classList.add('invalid');
          invalid.push(card);
          return;
        }}
        decided.push([card.dataset.id, decision, reviewer, notes]);
      }});
      if (invalid.length) {{
        alert(`有 ${{invalid.length}} 条已选择决定但缺少说明，已用红框标出。`);
        invalid[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});
        return;
      }}
      if (!decided.length) {{ alert('没有可导出的决定，请先选择至少一项。'); return; }}
      const rows = [['id', 'decision', 'reviewer', 'review_notes'], ...decided];
      const csv = rows.map(row => row.map(csvEscape).join(',')).join('\\n') + '\\n';
      const link = document.createElement('a');
      link.href = URL.createObjectURL(new Blob([csv], {{type: 'text/csv;charset=utf-8'}}));
      link.download = 'composition-review-decisions.csv';
      link.click();
      URL.revokeObjectURL(link.href);
    }});
  </script>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document)
    return len(cases)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=Path(__file__).with_name("manifest.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).with_name("review") / "review-queue.html"
    )
    args = parser.parse_args()
    print(f"generated review page for {generate_review_page(args.manifest, args.output)} candidates")


if __name__ == "__main__":
    main()
