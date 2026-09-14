const recording = {
  "case_id": "md-12620-terra-overnight-02",
  "commit": "63b2069e9685063c74abc41fae84a66f73e9e09b",
  "model": "gpt-5.6-terra",
  "reasoning": "medium",
  "usage": {
    "model_calls": 80,
    "input_tokens": 926267,
    "output_tokens": 15071
  },
  "checks": [
    {
      "name": "Regression before patch",
      "status": "pass",
      "detail": "Bug oracle triggered in 5/5 clean runs; the regression therefore fails on the pre-fix build.",
      "artifact": null,
      "baseline_artifact": null,
      "failing_tests": []
    },
    {
      "name": "Candidate build",
      "status": "pass",
      "detail": "Build exit code 0",
      "artifact": "md-12620-terra-overnight-02-542b50ef488b59dcc93d-candidate-build.log",
      "baseline_artifact": null,
      "failing_tests": []
    },
    {
      "name": "Existing tests",
      "status": "pass",
      "detail": "Test exit code 0.",
      "artifact": "md-12620-terra-overnight-02-5cc6f514bc42f3905fc4-candidate-tests.log",
      "baseline_artifact": "md-12620-terra-overnight-02-09dd9d34869a81b78f65-baseline-tests.log",
      "failing_tests": []
    },
    {
      "name": "Original replay after patch",
      "status": "pass",
      "detail": "5/5 reached expected state without the symptom; bug seen 0 times.",
      "artifact": null,
      "baseline_artifact": null,
      "failing_tests": []
    },
    {
      "name": "Smoke test",
      "status": "pass",
      "detail": "Clean desktop launch and live process after startup; deeper gameplay smoke coverage is not implemented.",
      "artifact": "md-12620-terra-overnight-02-1b55daffc0802b88d198-smoke.png",
      "baseline_artifact": null,
      "failing_tests": []
    }
  ],
  "actions": 30,
  "baseline": {
    "phase": "reduced-confirmation",
    "replay_event_seq": 2741,
    "recorded_verdict": {
      "observed": true,
      "confidence": 0.96,
      "explanation": "The screenshots demonstrate the reported persistence defect: a datapatch is visibly present, then the Patches UI reports none after deletion; after a visible save, exit, and reopening the named map, that datapatch is present again.",
      "evidence": [
        "md-12620-terra-overnight-02-66f8c1781de575431924-reduced-confirmation.png",
        "md-12620-terra-overnight-02-69835ebda2adeefab11f-reduced-confirmation.png",
        "md-12620-terra-overnight-02-5953793d6f55a4d1b623-reduced-confirmation.png",
        "md-12620-terra-overnight-02-77d35b543e27ef8f26f1-reduced-confirmation.png",
        "md-12620-terra-overnight-02-a861c3bee5959678a395-reduced-confirmation.png",
        "md-12620-terra-overnight-02-6dd9685c29a13060ee85-reduced-confirmation.png",
        "md-12620-terra-overnight-02-29e1e566558982307415-reduced-confirmation.png",
        "md-12620-terra-overnight-02-6020ead1fd0b0e515c4f-reduced-confirmation.png"
      ],
      "expected_state_reached": true,
      "symptom_absent": false
    },
    "frames": [
      {
        "label": "patch_present_before_initial_save",
        "event_seq": 2720,
        "recorded_at": "2026-09-14T17:36:11.290159+00:00",
        "sha256": "66f8c1781de57543192489afdd24c431922edaffcba4822efe691cc2bcfe4757",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-66f8c1781de575431924-reduced-confirmation.png"
      },
      {
        "label": "initial_map_save",
        "event_seq": 2722,
        "recorded_at": "2026-09-14T17:36:15.847753+00:00",
        "sha256": "69835ebda2adeefab11fe2bc9e9ede1e22abfd8d20fcf93f48ca45a8cbbb159a",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-69835ebda2adeefab11f-reduced-confirmation.png"
      },
      {
        "label": "persisted_patch_before_delete",
        "event_seq": 2725,
        "recorded_at": "2026-09-14T17:36:20.328405+00:00",
        "sha256": "5953793d6f55a4d1b623c100da985cd91502195b9b907e8373ee216337a76d59",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-5953793d6f55a4d1b623-reduced-confirmation.png"
      },
      {
        "label": "patch_deleted_ui",
        "event_seq": 2727,
        "recorded_at": "2026-09-14T17:36:23.973436+00:00",
        "sha256": "77d35b543e27ef8f26f1d8546149f0b413664f4946d2ac1efe8cac9de0e6cfbe",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-77d35b543e27ef8f26f1-reduced-confirmation.png"
      },
      {
        "label": "post_delete_map_save",
        "event_seq": 2730,
        "recorded_at": "2026-09-14T17:36:29.271232+00:00",
        "sha256": "a861c3bee5959678a395dc7c13ef72140784088b01c8024ceb3ea9f668e9bfeb",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-a861c3bee5959678a395-reduced-confirmation.png"
      },
      {
        "label": "exit_editor_after_deletion",
        "event_seq": 2732,
        "recorded_at": "2026-09-14T17:36:33.441477+00:00",
        "sha256": "6dd9685c29a13060ee8563b61f5be6d65efba86e1eb0a7806873757a1daecc06",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-6dd9685c29a13060ee85-reduced-confirmation.png"
      },
      {
        "label": "reopened_same_map",
        "event_seq": 2735,
        "recorded_at": "2026-09-14T17:36:47.638660+00:00",
        "sha256": "29e1e566558982307415f798868a0490f51b3e230d7d9e8dc95471e82132408d",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-29e1e566558982307415-reduced-confirmation.png"
      },
      {
        "label": "post_reopen_patch_state",
        "event_seq": 2739,
        "recorded_at": "2026-09-14T17:36:58.457045+00:00",
        "sha256": "6020ead1fd0b0e515c4f9e692ed53ae913b894327ec45c02241a48fdf9cd3ba7",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-6020ead1fd0b0e515c4f-reduced-confirmation.png"
      }
    ]
  },
  "candidate": {
    "phase": "post-patch",
    "replay_event_seq": 2815,
    "recorded_verdict": {
      "observed": false,
      "confidence": 0.98,
      "explanation": "The datapatch deletion persisted correctly in the tested map. A single patchset was visible before deletion; the editor then showed no patchsets, displayed a save confirmation, and—after reopening DatapatchPersistenceTest—still showed no patchsets. This is the expected behavior, not the reported reappearance defect.",
      "evidence": [
        "md-12620-terra-overnight-02-66f8c1781de575431924-post-patch.png",
        "md-12620-terra-overnight-02-a861c3bee5959678a395-post-patch.png",
        "md-12620-terra-overnight-02-5953793d6f55a4d1b623-post-patch.png",
        "md-12620-terra-overnight-02-77d35b543e27ef8f26f1-post-patch.png",
        "md-12620-terra-overnight-02-a861c3bee5959678a395-post-patch.png",
        "md-12620-terra-overnight-02-6dd9685c29a13060ee85-post-patch.png",
        "md-12620-terra-overnight-02-9a5fd1ef9a4f587da66b-post-patch.png",
        "md-12620-terra-overnight-02-2e0253837f7c1f5328b7-post-patch.png"
      ],
      "expected_state_reached": true,
      "symptom_absent": true
    },
    "frames": [
      {
        "label": "patch_present_before_initial_save",
        "event_seq": 2794,
        "recorded_at": "2026-09-14T17:41:57.245036+00:00",
        "sha256": "66f8c1781de57543192489afdd24c431922edaffcba4822efe691cc2bcfe4757",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-66f8c1781de575431924-post-patch.png"
      },
      {
        "label": "initial_map_save",
        "event_seq": 2796,
        "recorded_at": "2026-09-14T17:42:01.851787+00:00",
        "sha256": "a861c3bee5959678a395dc7c13ef72140784088b01c8024ceb3ea9f668e9bfeb",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-a861c3bee5959678a395-post-patch.png"
      },
      {
        "label": "persisted_patch_before_delete",
        "event_seq": 2799,
        "recorded_at": "2026-09-14T17:42:06.304703+00:00",
        "sha256": "5953793d6f55a4d1b623c100da985cd91502195b9b907e8373ee216337a76d59",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-5953793d6f55a4d1b623-post-patch.png"
      },
      {
        "label": "patch_deleted_ui",
        "event_seq": 2801,
        "recorded_at": "2026-09-14T17:42:09.813498+00:00",
        "sha256": "77d35b543e27ef8f26f1d8546149f0b413664f4946d2ac1efe8cac9de0e6cfbe",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-77d35b543e27ef8f26f1-post-patch.png"
      },
      {
        "label": "post_delete_map_save",
        "event_seq": 2804,
        "recorded_at": "2026-09-14T17:42:15.130897+00:00",
        "sha256": "a861c3bee5959678a395dc7c13ef72140784088b01c8024ceb3ea9f668e9bfeb",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-a861c3bee5959678a395-post-patch.png"
      },
      {
        "label": "exit_editor_after_deletion",
        "event_seq": 2806,
        "recorded_at": "2026-09-14T17:42:19.216588+00:00",
        "sha256": "6dd9685c29a13060ee8563b61f5be6d65efba86e1eb0a7806873757a1daecc06",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-6dd9685c29a13060ee85-post-patch.png"
      },
      {
        "label": "reopened_same_map",
        "event_seq": 2809,
        "recorded_at": "2026-09-14T17:42:33.315561+00:00",
        "sha256": "9a5fd1ef9a4f587da66bb81fbc62966cd15920c0ff26bec3908053bf998a4b1a",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-9a5fd1ef9a4f587da66b-post-patch.png"
      },
      {
        "label": "post_reopen_patch_state",
        "event_seq": 2813,
        "recorded_at": "2026-09-14T17:42:44.045262+00:00",
        "sha256": "2e0253837f7c1f5328b724f1e1f3075c4e1f642249530e55902d25187e7f1695",
        "url": "../../evidence/overnight-2026-09-15/md-12620-terra-overnight-02/artifacts/md-12620-terra-overnight-02-2e0253837f7c1f5328b7-post-patch.png"
      }
    ]
  },
  "patch": "diff --git a/core/src/mindustry/editor/data/MapPatchesView.java b/core/src/mindustry/editor/data/MapPatchesView.java\nindex b814576..b53bef9 100644\n--- a/core/src/mindustry/editor/data/MapPatchesView.java\n+++ b/core/src/mindustry/editor/data/MapPatchesView.java\n@@ -84,6 +84,7 @@ public class MapPatchesView implements AssetView{\n             list.button(Icon.trash, Styles.graySquarei, iconMed, () -> {\n                 ui.showConfirm(\"@patch.delete.confirm\",  () -> {\n                     patches.remove(patch);\n+                    state.data.reloadPatches(patches);\n                     diag.rebuild();\n                 });\n             }).size(h);\n",
  "patch_sha256": "8a4309b8ce8b10655f1ba09315b0ab5e11819f0f87ec7c9fff839d3d13394090",
  "note": "Eight selected recorded checkpoints from one baseline and one candidate replay. Intermediate actions are omitted. This is not real-time video or a new execution."
};
