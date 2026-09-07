/**
 * markdown.ts --- the small subset of markdown an agent's answer arrives in
 *
 * Models answer in markdown whether or not they are asked to, so a reply
 * rendered as plain text reads as literal asterisks. This parses the subset
 * they actually use — headings, lists, fenced code, bold, italic, inline code —
 * rather than pulling in a full markdown stack for a chat bubble.
 *
 * Contains:
 *   InlineToken: one run of text inside a block, with its emphasis
 *   Block: one block-level element of an answer
 *   INLINE_PATTERN: matches the emphasis markers, longest marker first
 *   parseInline(): splits one line into emphasised and plain runs
 *   parseBlocks(): splits an answer into headings, lists, code, and paragraphs
 */

export type InlineToken =
  | { kind: "text"; text: string }
  | { kind: "bold"; text: string }
  | { kind: "italic"; text: string }
  | { kind: "code"; text: string };

export type Block =
  | { kind: "heading"; level: number; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "bullets"; items: string[] }
  | { kind: "numbers"; items: string[] }
  | { kind: "code"; text: string };

// Bold is matched before italic on purpose: "**a**" would otherwise be read as
// an italic "*a*" wrapped in stray asterisks.
const INLINE_PATTERN = /\*\*([^*]+)\*\*|`([^`]+)`|\*([^*\n]+)\*|_([^_\n]+)_/g;

const HEADING = /^(#{1,6})\s+(.*)$/;
const BULLET = /^\s*[-*+]\s+(.*)$/;
const NUMBER = /^\s*\d+[.)]\s+(.*)$/;
const FENCE = /^\s*```/;

/**
 * Splits one line into emphasised and plain runs.
 *
 * @param line - The line to split.
 * @returns tokens - The line's runs in order, plain text included.
 */
export function parseInline(line: string): InlineToken[] {
  const tokens: InlineToken[] = [];
  let cursor = 0;
  INLINE_PATTERN.lastIndex = 0;
  for (
    let match = INLINE_PATTERN.exec(line);
    match !== null;
    match = INLINE_PATTERN.exec(line)
  ) {
    if (match.index > cursor) {
      tokens.push({ kind: "text", text: line.slice(cursor, match.index) });
    }
    const [, bold, code, star, underscore] = match;
    if (bold !== undefined) {
      tokens.push({ kind: "bold", text: bold });
    } else if (code !== undefined) {
      tokens.push({ kind: "code", text: code });
    } else {
      tokens.push({ kind: "italic", text: star ?? underscore ?? "" });
    }
    cursor = match.index + match[0].length;
  }
  if (cursor < line.length) {
    tokens.push({ kind: "text", text: line.slice(cursor) });
  }
  return tokens;
}

/**
 * Splits an answer into the block-level elements it is written in.
 *
 * @param text - The whole answer, as the model wrote it.
 * @returns blocks - The answer's blocks in order.
 */
export function parseBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  const lines = text.split("\n");
  let paragraph: string[] = [];

  const flush = () => {
    if (paragraph.length > 0) {
      blocks.push({ kind: "paragraph", text: paragraph.join("\n") });
      paragraph = [];
    }
  };

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];

    if (FENCE.test(line)) {
      flush();
      const body: string[] = [];
      index += 1;
      while (index < lines.length && !FENCE.test(lines[index])) {
        body.push(lines[index]);
        index += 1;
      }
      blocks.push({ kind: "code", text: body.join("\n") });
      continue;
    }

    const heading = HEADING.exec(line);
    if (heading !== null) {
      flush();
      blocks.push({
        kind: "heading",
        level: heading[1].length,
        text: heading[2],
      });
      continue;
    }

    const bullet = BULLET.exec(line);
    const numbered = NUMBER.exec(line);
    if (bullet !== null || numbered !== null) {
      flush();
      const kind = bullet !== null ? "bullets" : "numbers";
      const last = blocks[blocks.length - 1];
      const item = (bullet ?? numbered)![1];
      if (last !== undefined && last.kind === kind) {
        last.items.push(item);
      } else {
        blocks.push({ kind, items: [item] });
      }
      continue;
    }

    if (line.trim() === "") {
      flush();
      continue;
    }
    paragraph.push(line);
  }

  flush();
  return blocks;
}
