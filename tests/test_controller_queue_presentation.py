from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUEUE_PRESENTATION_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/controller_queue_presentation_cases.json"
)

QUEUE_PRESENTATION_CASES = json.loads(
    QUEUE_PRESENTATION_FIXTURE.read_text(encoding="utf-8")
)

QUEUE_PRESENTATION_CONTRACT_TEMPLATE = """
const basePayload = {
  runtime_state: 'RUNNING',
  automation_health: 'ok',
  automation_reason_code: '',
  stale_advisory_pending: false,
  control_age_cycles: 0,
  control: {
    active_control_status: 'none',
    active_control_seq: -1,
    active_control_file: '',
  },
  active_round: null,
  watcher: { alive: true },
};

const queuePresentationCases = __QUEUE_PRESENTATION_CASES__;

function payload(overrides = {}) {
  return {
    ...basePayload,
    ...overrides,
    control: { ...basePayload.control, ...(overrides.control || {}) },
  };
}

function assertQueuePresentation(queueFields) {
  for (const testCase of queuePresentationCases) {
    assert.deepEqual(
      queueFields(payload(testCase.overrides)),
      testCase.expected,
      testCase.name,
    );
  }
}
"""


class ControllerQueuePresentationTests(unittest.TestCase):
    def _queue_contract_script(self) -> str:
        return QUEUE_PRESENTATION_CONTRACT_TEMPLATE.replace(
            "__QUEUE_PRESENTATION_CASES__",
            json.dumps(QUEUE_PRESENTATION_CASES, sort_keys=True),
        )

    def _run_node_script(self, script: str, label: str) -> None:
        result = subprocess.run(
            ["node", "--input-type=module", "-"],
            input=textwrap.dedent(script),
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        if result.returncode != 0:
            self.fail(
                f"{label} failed\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

    def test_runtime_payloads_drive_queue_presentation(self) -> None:
        script = """
            import { strict as assert } from 'node:assert';
            import { PipelineState } from './controller/js/state.js';

            __QUEUE_PRESENTATION_CONTRACT__

            function queueFields(runtimePayload) {
              const presentation = PipelineState.getPresentation(runtimePayload);
              return {
                noQueuedPipelineTask: presentation.noQueuedPipelineTask,
                pipelineQueueStatus: presentation.pipelineQueueStatus,
                pipelineQueueClass: presentation.pipelineQueueClass,
              };
            }

            assertQueuePresentation(queueFields);
            """.replace(
                "__QUEUE_PRESENTATION_CONTRACT__",
                self._queue_contract_script(),
            )
        self._run_node_script(
            script,
            "controller Queue presentation Node check",
        )

    def test_cozy_queue_presentation_matches_runtime_payloads_without_socket(self) -> None:
        script = """
            import { strict as assert } from 'node:assert';
            import { readFileSync } from 'node:fs';

            const source = readFileSync('./controller/js/cozy.js', 'utf8');
            const queuePresentationSource = readFileSync('./controller/js/queue-presentation.js', 'utf8');

            function extractFunction(name) {
              const start = source.indexOf(`function ${name}(`);
              assert.notEqual(start, -1, `${name} exists in cozy.js`);
              const bodyStart = source.indexOf('{', start);
              assert.notEqual(bodyStart, -1, `${name} has a body`);
              let depth = 0;
              for (let index = bodyStart; index < source.length; index += 1) {
                const char = source[index];
                if (char === '{') depth += 1;
                if (char === '}') {
                  depth -= 1;
                  if (depth === 0) return source.slice(start, index + 1);
                }
              }
              throw new Error(`Could not extract ${name}`);
            }

            const cozyPresentation = new Function(`
              const INACTIVE_RUNTIME_STATES = new Set(['STOPPED', 'STOPPING', 'BROKEN']);
              const UNCERTAIN_RUNTIME_REASONS = new Set([
                'supervisor_missing_recent_ambiguous',
                'supervisor_missing_snapshot_undated',
              ]);
              ${queuePresentationSource}
              ${extractFunction('queuePresentationHelper')}
              ${extractFunction('currentTurnState')}
              ${extractFunction('liveRoundState')}
              ${extractFunction('isSuppressedOperatorCandidate')}
              ${extractFunction('isNoQueuedPipelineTask')}
              ${extractFunction('pipelineQueuePresentation')}
              ${extractFunction('getPresentation')}
              return { getPresentation };
            `)();

            __QUEUE_PRESENTATION_CONTRACT__

            function queueFields(runtimePayload) {
              const presentation = cozyPresentation.getPresentation(runtimePayload);
              return {
                noQueuedPipelineTask: presentation.noQueuedPipelineTask,
                pipelineQueueStatus: presentation.pipelineQueueStatus,
                pipelineQueueClass: presentation.pipelineQueueClass,
              };
            }

            assertQueuePresentation(queueFields);
            """.replace(
                "__QUEUE_PRESENTATION_CONTRACT__",
                self._queue_contract_script(),
            )
        self._run_node_script(
            script,
            "cozy Queue presentation socket-free Node check",
        )

    def test_cozy_queue_presentation_reaches_rendered_surfaces_without_socket(
        self,
    ) -> None:
        script = """
            import { strict as assert } from 'node:assert';
            import { readFileSync } from 'node:fs';

            const source = readFileSync('./controller/js/cozy.js', 'utf8');
            const queuePresentationSource = readFileSync('./controller/js/queue-presentation.js', 'utf8');

            function extractFunction(name) {
              const start = source.indexOf(`function ${name}(`);
              assert.notEqual(start, -1, `${name} exists in cozy.js`);
              const bodyStart = source.indexOf('{', start);
              assert.notEqual(bodyStart, -1, `${name} has a body`);
              let depth = 0;
              for (let index = bodyStart; index < source.length; index += 1) {
                const char = source[index];
                if (char === '{') depth += 1;
                if (char === '}') {
                  depth -= 1;
                  if (depth === 0) return source.slice(start, index + 1);
                }
              }
              throw new Error(`Could not extract ${name}`);
            }

            function extractFunctionRange(startName, nextName) {
              const start = source.indexOf(`function ${startName}(`);
              assert.notEqual(start, -1, `${startName} exists in cozy.js`);
              const end = source.indexOf(`function ${nextName}(`, start);
              assert.notEqual(end, -1, `${nextName} follows ${startName}`);
              return source.slice(start, end);
            }

            const renderedSurfaces = new Function(`
              const INACTIVE_RUNTIME_STATES = new Set(['STOPPED', 'STOPPING', 'BROKEN']);
              const UNCERTAIN_RUNTIME_REASONS = new Set([
                'supervisor_missing_recent_ambiguous',
                'supervisor_missing_snapshot_undated',
              ]);
              const runtimeStateStore = {
                data: null,
                inspector: { selectedAgent: '' },
                monitor: { connected: false, snapshot: null },
              };
              const agents = [];
              const elements = new Map([
                ['tab-content', { innerHTML: '' }],
                ['marquee-text', {
                  textContent: '',
                  style: {},
                  get offsetWidth() { return 0; },
                }],
              ]);
              const document = {
                getElementById(id) {
                  return elements.get(id) || null;
                },
              };
              let lastMarqueeText = '';
              function esc(value) {
                return String(value ?? '').replace(/[&<>]/g, (char) => ({
                  '&': '&amp;',
                  '<': '&lt;',
                  '>': '&gt;',
                }[char]));
              }
              function truncate(value, max) {
                const text = String(value || '');
                return text.length > max ? text.slice(0, max - 1) + '…' : text;
              }
              function basename(value) {
                const parts = String(value || '').split('/').filter(Boolean);
                return parts.length ? parts[parts.length - 1] : '—';
              }
              function renderTokenHud() { return ''; }
              function roleOwnerRows() { return ''; }
              ${queuePresentationSource}
              ${extractFunction('queuePresentationHelper')}
              ${extractFunction('currentTurnState')}
              ${extractFunction('liveRoundState')}
              ${extractFunction('isSuppressedOperatorCandidate')}
              ${extractFunction('isNoQueuedPipelineTask')}
              ${extractFunction('pipelineQueuePresentation')}
              ${extractFunction('getPresentation')}
              ${extractFunctionRange('restartMarqueeAnimation', 'pushEvent')}
              ${extractFunctionRange('renderSidebar', 'applyRuntimeStatusData')}
              return {
                elements,
                renderSidebar,
                runtimeStateStore,
                updateMarqueeFromState,
                reset() {
                  elements.get('tab-content').innerHTML = '';
                  elements.get('marquee-text').textContent = '';
                  elements.get('marquee-text').style.animation = '';
                  lastMarqueeText = '';
                },
              };
            `)();

            __QUEUE_PRESENTATION_CONTRACT__

            const queueRowPattern = /<div class="info-row"><span class="info-label">(Queue|큐)<\\/span><span class="info-value ([^"]+)">([^<]+)<\\/span><\\/div>/;
            function escapeRegExp(value) {
              return String(value).replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
            }

            for (const testCase of queuePresentationCases) {
              const runtimePayload = payload(testCase.overrides);
              const expected = testCase.expected;
              renderedSurfaces.reset();
              renderedSurfaces.runtimeStateStore.data = runtimePayload;

              renderedSurfaces.renderSidebar();
              renderedSurfaces.updateMarqueeFromState(runtimePayload);

              const sidebarHtml = renderedSurfaces.elements.get('tab-content').innerHTML;
              const queueMatch = sidebarHtml.match(queueRowPattern);
              assert.notEqual(queueMatch, null, `${testCase.name} Queue row rendered`);
              assert.equal(
                queueMatch[2],
                expected.pipelineQueueClass,
                `${testCase.name} Queue row class`,
              );
              assert.equal(
                queueMatch[3],
                expected.pipelineQueueStatus,
                `${testCase.name} Queue row text`,
              );
              assert.match(
                renderedSurfaces.elements.get('marquee-text').textContent,
                new RegExp(`(Queue|대기열) ${escapeRegExp(expected.pipelineQueueStatus)}`),
                `${testCase.name} marquee Queue text`,
              );
            }
            """.replace(
                "__QUEUE_PRESENTATION_CONTRACT__",
                self._queue_contract_script(),
            )
        self._run_node_script(
            script,
            "cozy Queue presentation rendered surface socket-free Node check",
        )


if __name__ == "__main__":
    unittest.main()
