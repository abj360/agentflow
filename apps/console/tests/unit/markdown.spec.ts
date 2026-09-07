/**
 * markdown.spec.ts --- tests for the markdown subset an answer arrives in
 *
 * Contains:
 *   inline specs: bold, italic, inline code, and plain runs
 *   block specs: headings, lists, fenced code, and paragraphs
 */

import { expect, test } from "@playwright/test";

import { parseBlocks, parseInline } from "../../lib/markdown";

test("bold wins over italic on a double asterisk", () => {
  expect(parseInline("a **b** c")).toEqual([
    { kind: "text", text: "a " },
    { kind: "bold", text: "b" },
    { kind: "text", text: " c" },
  ]);
});

test("a single asterisk is italic", () => {
  expect(parseInline("*b*")).toEqual([{ kind: "italic", text: "b" }]);
});

test("an underscore pair is italic too", () => {
  expect(parseInline("_b_")).toEqual([{ kind: "italic", text: "b" }]);
});

test("a backtick run is code", () => {
  expect(parseInline("call `run()` now")[1]).toEqual({
    kind: "code",
    text: "run()",
  });
});

test("a line with no markers is one plain run", () => {
  expect(parseInline("nothing here")).toEqual([
    { kind: "text", text: "nothing here" },
  ]);
});

test("an empty line produces no runs", () => {
  expect(parseInline("")).toEqual([]);
});

test("a heading carries its level", () => {
  expect(parseBlocks("## Risks")).toEqual([
    { kind: "heading", level: 2, text: "Risks" },
  ]);
});

test("consecutive bullets become one list", () => {
  expect(parseBlocks("- one\n- two")).toEqual([
    { kind: "bullets", items: ["one", "two"] },
  ]);
});

test("numbered items become their own list", () => {
  expect(parseBlocks("1. one\n2. two")).toEqual([
    { kind: "numbers", items: ["one", "two"] },
  ]);
});

test("a fenced block is code, markers dropped", () => {
  expect(parseBlocks("```\nrun()\n```")).toEqual([
    { kind: "code", text: "run()" },
  ]);
});

test("a blank line separates two paragraphs", () => {
  expect(parseBlocks("one\n\ntwo")).toEqual([
    { kind: "paragraph", text: "one" },
    { kind: "paragraph", text: "two" },
  ]);
});

test("lines inside one paragraph are kept together", () => {
  expect(parseBlocks("one\ntwo")).toEqual([
    { kind: "paragraph", text: "one\ntwo" },
  ]);
});

test("an empty answer produces no blocks", () => {
  expect(parseBlocks("")).toEqual([]);
});

test("a heading interrupts the paragraph before it", () => {
  const blocks = parseBlocks("intro\n## Heading\nbody");
  expect(blocks.map((block) => block.kind)).toEqual([
    "paragraph",
    "heading",
    "paragraph",
  ]);
});
