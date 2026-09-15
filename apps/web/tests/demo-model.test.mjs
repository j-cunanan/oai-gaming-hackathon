import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { matchReport, demoLocation } from "../src/demo-model.ts";

const catalog = JSON.parse(
  fs.readFileSync(new URL("../demo/catalog.json", import.meta.url), "utf8"),
).map((c) => ({ ...c, game: "mindustry" }));
test("report paraphrases match their object and multistep symptom", () => {
  for (const [report, id] of [
    [
      "After removing a datapatch, I save and reload the map and it reappears.",
      "datapatch",
    ],
    [
      "Mindustry map editor: I deleted the data patch but it came back on reopening.",
      "datapatch",
    ],
    ["Saving a map containing a target dummy causes a crash.", "target-dummy"],
    ["Colored floor picker changes my hex color when I confirm it.", "color"],
  ]) {
    const result = matchReport(report, "mindustry", catalog);
    assert.equal(result[0].record.id, id);
    assert.equal(result[0].strength, "strong");
  }
});
test("unrelated, healthy and other-game reports do not force a demo match", () => {
  for (const report of [
    "The multiplayer server disconnects after joining.",
    "The map crashes on save.",
    "Deleting a data patch works: it does not return when I reopen the save.",
    "The target dummy does not crash when I save.",
    "Minecraft colored wall changes when I enter a hex color.",
  ])
    assert.deepEqual(matchReport(report, "mindustry", catalog), [], report);
  assert.deepEqual(matchReport(catalog[0].sampleReport, "luanti", catalog), []);
});
test("partial reports expose missing evidence and ambiguous reports retain choices", () => {
  const partial = matchReport(
    "I deleted a data patch in the editor.",
    "mindustry",
    catalog,
  );
  assert.equal(partial[0].strength, "possible");
  assert.ok(partial[0].missing.length);
  const mixed = matchReport(
    "Saving a Target Dummy crashes. Deleted datapatches return after reopening a map.",
    "mindustry",
    catalog,
  );
  assert.deepEqual(
    new Set(mixed.map((m) => m.record.id)),
    new Set(["datapatch", "target-dummy"]),
  );
});
test("only exact upstream issue URLs match by report identity", () => {
  assert.equal(
    matchReport(
      "https://github.com/Anuken/Mindustry/issues/12620",
      "mindustry",
      catalog,
    )[0].record.id,
    "datapatch",
  );
  for (const report of [
    "https://github.com/not-anuken/Mindustry/issues/12620",
    "https://github.com/Anuken/Mindustry/issues/1262099",
    "https://example.com/issues/12620",
  ])
    assert.deepEqual(matchReport(report, "mindustry", catalog), []);
});
test("share links preserve a supported stage; invalid stages return to report", () => {
  assert.deepEqual(demoLocation("?view=demo&demo=color&stage=validate"), {
    id: "color",
    stage: "validate",
  });
  assert.deepEqual(demoLocation("?demo=unknown&stage=live"), {
    id: "unknown",
    stage: "report",
  });
});
